"""
第 9 模块：相机对焦能力探测与清晰预览。

先探测当前镜头和 CanMV 固件是否真正提供自动对焦接口；仅当接口可用时才启用。
本程序不控制变焦，也不进行 UART 通信。
"""

import gc
import os
import time

from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager


# ============================= 现场标定区 =============================
# 用于目视调焦的输出分辨率。保持 4:3，避免预览画面变形干扰判断。
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

# 仅在 API 探测成功后生效；设为 False 可只查询能力而不请求自动对焦。
ENABLE_AUTO_FOCUS = True
PRINT_PERIOD_FRAMES = 30


def query_and_enable_auto_focus(sensor):
    """安全查询镜头的 AF 能力，只有当前固件提供接口才尝试打开自动对焦。"""
    caps = "focus_caps unavailable"
    state_before = "auto_focus unavailable"
    state_after = state_before

    focus_caps = getattr(sensor, "focus_caps", None)
    if callable(focus_caps):
        try:
            caps = focus_caps()
        except BaseException as error:
            caps = "focus_caps error: %s" % error

    auto_focus = getattr(sensor, "auto_focus", None)
    if not callable(auto_focus):
        return caps, state_before, state_after, False

    try:
        state_before = auto_focus()
        if ENABLE_AUTO_FOCUS:
            auto_focus(True)
        state_after = auto_focus()
        return caps, state_before, state_after, True
    except BaseException as error:
        state_after = "auto_focus error: %s" % error
        return caps, state_before, state_after, False


def draw_focus_guide(frame, auto_focus_available, auto_focus_state, fps):
    """绘制中心取景框和 AF 状态，让镜头调焦时有固定参考区域。"""
    guide_width = FRAME_WIDTH // 2
    guide_height = FRAME_HEIGHT // 2
    guide_x = (FRAME_WIDTH - guide_width) // 2
    guide_y = (FRAME_HEIGHT - guide_height) // 2

    frame.draw_rectangle(
        guide_x, guide_y, guide_width, guide_height, color=(255, 255, 0), thickness=2
    )
    frame.draw_cross(FRAME_WIDTH // 2, FRAME_HEIGHT // 2, color=(255, 0, 0), size=14)

    if auto_focus_available:
        status = "AF=%s" % auto_focus_state
        color = (0, 255, 0)
    else:
        status = "AF unsupported: manual lens focus"
        color = (255, 80, 80)

    frame.draw_string_advanced(0, 0, 18, status, color=color)
    frame.draw_string_advanced(0, 24, 16, "FPS: %.1f" % fps, color=(255, 255, 255))


def main():
    """以原始 RGB565 预览显示当前镜头清晰度，并打印自动对焦能力。"""
    sensor = None
    frame_count = 0

    try:
        # 已由本板日志确认 GC2093 使用 CSI2，对应 CanMV 中的 Sensor id=2。
        sensor = Sensor(id=2, width=FRAME_WIDTH, height=FRAME_HEIGHT, fps=30)
        sensor.reset()
        sensor.set_framesize(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        sensor.set_pixformat(Sensor.RGB565)

        caps, state_before, state_after, auto_focus_available = query_and_enable_auto_focus(sensor)
        print("focus caps=%s" % caps)
        print("auto focus before=%s after=%s" % (state_before, state_after))

        Display.init(
            Display.ST7701,
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            to_ide=True,
        )
        MediaManager.init()
        sensor.run()

        clock = time.clock()
        while True:
            clock.tick()
            os.exitpoint()
            frame = sensor.snapshot()
            frame_count += 1

            draw_focus_guide(frame, auto_focus_available, state_after, clock.fps())
            Display.show_image(frame)

            if frame_count % PRINT_PERIOD_FRAMES == 0:
                print("focus preview fps=%.1f af=%s" % (clock.fps(), state_after))
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("focus preview error: %s" % error)
    finally:
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
