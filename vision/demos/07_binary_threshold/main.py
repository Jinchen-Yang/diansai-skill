"""
第 7 模块：亚博 K230 RGB888 二值化预处理。

本模块只负责将图像变为黑白图，不做矩形检测、数字识别或主控通信。
"""

import gc
import os
import time

import cv_lite
from media.sensor import *
from media.display import *
from media.media import *
import image


# ============================= 现场标定区 =============================
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

# 低于阈值的像素为黑，高于阈值的像素为白。
BINARY_THRESHOLD = 130
BINARY_MAX_VALUE = 255
PRINT_PERIOD_FRAMES = 15


def main():
    """运行 RGB888 图像二值化并显示黑白结果。"""
    sensor = None
    frame_count = 0

    try:
        sensor = Sensor(id=2, width=640, height=480, fps=30)
        sensor.reset()
        sensor.set_framesize(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        sensor.set_pixformat(Sensor.RGB888)

        Display.init(
            Display.ST7701,
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            to_ide=True,
            quality=50,
        )
        MediaManager.init()
        sensor.run()

        clock = time.clock()
        while True:
            clock.tick()
            os.exitpoint()
            frame = sensor.snapshot()
            frame_count += 1

            binary_np = cv_lite.rgb888_threshold_binary(
                [FRAME_HEIGHT, FRAME_WIDTH],
                frame.to_numpy_ref(),
                BINARY_THRESHOLD,
                BINARY_MAX_VALUE,
            )
            binary_frame = image.Image(
                FRAME_WIDTH,
                FRAME_HEIGHT,
                image.GRAYSCALE,
                alloc=image.ALLOC_REF,
                data=binary_np,
            )

            binary_frame.draw_string_advanced(
                0,
                0,
                16,
                "THR=%d FPS: %.1f" % (BINARY_THRESHOLD, clock.fps()),
                color=(255, 255, 255),
            )
            Display.show_image(binary_frame)

            if frame_count % PRINT_PERIOD_FRAMES == 0:
                print("threshold=%d fps=%.1f" % (BINARY_THRESHOLD, clock.fps()))
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("binary threshold error: %s" % error)
    finally:
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
