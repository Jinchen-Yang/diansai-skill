"""
第 6 模块：亚博 K230 AprilTag 识别。
本文件只负责检测、标注和输出 AprilTag 结果，不接 UART。
"""

import gc
import math
import os
import time

from media.sensor import *
from media.display import *
from media.media import *


# ============================= 现场标定区 =============================
FRAME_WIDTH = 400
FRAME_HEIGHT = 240
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

# 只打开比赛实际会用到的家族，可减少误检和计算量。
TAG_FAMILIES = 0
TAG_FAMILIES |= image.TAG36H11

PRINT_PERIOD_FRAMES = 15
MAX_LABEL_CHARS = 24


FAMILY_NAMES = {
    image.TAG16H5: "TAG16H5",
    image.TAG25H7: "TAG25H7",
    image.TAG25H9: "TAG25H9",
    image.TAG36H10: "TAG36H10",
    image.TAG36H11: "TAG36H11",
    image.ARTOOLKIT: "ARTOOLKIT",
}


def family_name(tag):
    """将 AprilTag 家族位掩码转换为可读名称。"""
    return FAMILY_NAMES.get(tag.family(), "UNKNOWN")


def tag_result(tag):
    """提取后续统一视觉接口需要的 ID、中心、矩形和角度。"""
    x, y, width, height = tag.rect()
    return {
        "family": family_name(tag),
        "id": int(tag.id()),
        "cx": int(tag.cx()),
        "cy": int(tag.cy()),
        "x": int(x),
        "y": int(y),
        "w": int(width),
        "h": int(height),
        "rotation_deg": (180.0 * tag.rotation()) / math.pi,
    }


def draw_tag(image, index, result):
    """在画面上标出 Tag 框、中心、ID 和旋转角。"""
    rect = (result["x"], result["y"], result["w"], result["h"])
    label = "T%d ID=%d %.1fdeg" % (index, result["id"], result["rotation_deg"])
    if len(label) > MAX_LABEL_CHARS:
        label = label[:MAX_LABEL_CHARS]

    image.draw_rectangle(rect, color=(255, 0, 0), thickness=3)
    image.draw_cross(result["cx"], result["cy"], color=(0, 255, 0), size=10)
    image.draw_string_advanced(
        result["x"],
        max(0, result["y"] - 20),
        14,
        label,
        color=(255, 255, 0),
    )


def main():
    """运行 AprilTag 检测并低频输出结构化调试结果。"""
    sensor = None
    previous_signature = None
    frame_count = 0

    try:
        sensor = Sensor()
        sensor.reset()
        sensor.set_framesize(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        sensor.set_pixformat(Sensor.RGB565)

        Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
        MediaManager.init()
        sensor.run()

        display_x = (DISPLAY_WIDTH - FRAME_WIDTH) // 2
        display_y = (DISPLAY_HEIGHT - FRAME_HEIGHT) // 2
        clock = time.clock()

        while True:
            clock.tick()
            os.exitpoint()
            image = sensor.snapshot()
            frame_count += 1

            results = []
            for index, tag in enumerate(image.find_apriltags(families=TAG_FAMILIES), start=1):
                result = tag_result(tag)
                results.append(result)
                draw_tag(image, index, result)

            image.draw_string_advanced(
                0,
                0,
                16,
                "APRILTAG=%d FPS: %.1f" % (len(results), clock.fps()),
                color=(255, 255, 255),
            )
            Display.show_image(image, x=display_x, y=display_y)

            signature = tuple(
                (item["family"], item["id"], item["cx"], item["cy"], round(item["rotation_deg"], 1))
                for item in results
            )
            if signature != previous_signature or frame_count % PRINT_PERIOD_FRAMES == 0:
                print("apriltag count=%d results=%s" % (len(results), results))
                previous_signature = signature
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("apriltag error: %s" % error)
    finally:
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
