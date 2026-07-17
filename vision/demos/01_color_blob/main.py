"""第 1 模块：亚博 K230 单文件多色块识别示例。

直接由 CanMV IDE 运行。本阶段只在屏幕/IDE 上输出识别结果，不依赖主控串口。
所有现场参数都集中在“配置区”，不要在算法循环中散写阈值。
"""

import gc
import os
import time

from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager


# ============================= 现场标定配置区 =============================
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# 每项格式：名称、LAB 阈值、调试框颜色。
# 下列值仅来自亚博示例的起始值，必须在实际场地灯光下重新标定。
COLOR_SPECS = (
    ("RED", (0, 66, 7, 127, 3, 127), (255, 0, 0)),
    ("GREEN", (42, 100, -128, -17, 6, 66), (0, 255, 0)),
    ("BLUE", (43, 99, -43, -4, -56, -7), (0, 0, 255)),
)

# 过滤小噪点。应根据目标在画面中的最小尺寸调整，而不是为了“有结果”盲目调低。
MIN_PIXELS = 150
MIN_AREA = 300
MERGE_MARGIN = 5

# 同一颜色连续识别到该帧数才显示“STABLE”，后续向主控发任务结果时也沿用该规则。
STABLE_FRAMES = 3
PRINT_PERIOD_FRAMES = 15


def largest_blob(image, threshold):
    """返回满足阈值的最大色块；无有效目标时返回 None。"""
    blobs = image.find_blobs(
        [threshold],
        pixels_threshold=MIN_PIXELS,
        area_threshold=MIN_AREA,
        merge=True,
        margin=MERGE_MARGIN,
    )
    if not blobs:
        return None
    return max(blobs, key=lambda blob: blob.pixels())


def draw_blob(image, blob, name, color, stable_count):
    """叠加目标框、中心、坐标和稳定性状态，便于观察误识别来自哪里。"""
    image.draw_rectangle(blob.rect(), color=color, thickness=3)
    image.draw_cross(blob.cx(), blob.cy(), color=color, size=10)
    state = "STABLE" if stable_count >= STABLE_FRAMES else "CHECK"
    label = "%s %s (%d,%d)" % (name, state, blob.cx(), blob.cy())
    image.draw_string_advanced(blob.x(), max(0, blob.y() - 22), 18, label, color=color)


def main():
    """初始化相机后逐帧寻找红、绿、蓝的最大候选色块。"""
    sensor = None
    stable_counts = [0] * len(COLOR_SPECS)

    try:
        sensor = Sensor()
        sensor.reset()
        sensor.set_framesize(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        sensor.set_pixformat(Sensor.RGB565)

        Display.init(Display.ST7701, width=FRAME_WIDTH, height=FRAME_HEIGHT, to_ide=True)
        MediaManager.init()
        sensor.run()

        clock = time.clock()
        frame_count = 0
        while True:
            clock.tick()
            os.exitpoint()
            image = sensor.snapshot()
            frame_count += 1

            summary = []
            for index in range(len(COLOR_SPECS)):
                name, threshold, color = COLOR_SPECS[index]
                blob = largest_blob(image, threshold)
                if blob is None:
                    stable_counts[index] = 0
                    continue

                stable_counts[index] += 1
                draw_blob(image, blob, name, color, stable_counts[index])
                summary.append("%s:%d,%d" % (name, blob.cx(), blob.cy()))

            image.draw_string_advanced(0, 0, 20, "FPS: %.1f" % clock.fps(), color=(255, 255, 255))
            image.draw_string_advanced(
                0,
                24,
                16,
                "blob demo | LAB threshold",
                color=(255, 255, 0),
            )
            Display.show_image(image)

            if frame_count % PRINT_PERIOD_FRAMES == 0:
                print("frame=%d %s" % (frame_count, " ".join(summary) if summary else "no target"))
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("color blob error: %s" % error)
    finally:
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
