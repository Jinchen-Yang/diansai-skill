"""第 3 模块：亚博 K230 CV Lite 灰度霍夫圆检测。
本文件是后续集成时要复用的圆形算法核。独立运行，暂不依赖主控串口。
"""

import gc
import os
import time

import cv_lite
import ulab.numpy as np
from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager


# ============================= 现场标定区 =============================
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

# 参数顺序与亚博 06.cv_lite/4.rgb888_find_circles.py 保持一致。
CIRCLE_IMAGE_SHAPE = [FRAME_HEIGHT, FRAME_WIDTH]
HOUGH_DP = 1
MIN_CENTER_DISTANCE = 30
CANNY_HIGH_THRESHOLD = 90
ACCUMULATOR_THRESHOLD = 30
MIN_RADIUS = 10
MAX_RADIUS = 80

TRACK_CENTER_DELTA = 18
TRACK_RADIUS_DELTA = 10
STABLE_FRAMES = 3
PRINT_PERIOD_FRAMES = 15


def circle_tuples(raw_values):
    """将 CV Lite 返回的 [x, y, r, ...] 数组转为圆元组列表。"""
    circles = []
    for index in range(0, len(raw_values) - 2, 3):
        circles.append((int(raw_values[index]), int(raw_values[index + 1]), int(raw_values[index + 2])))
    return circles


def select_main_circle(circles):
    """保留半径合法的候选圆，以最大圆作为主目标。"""
    candidates = []
    for x, y, radius in circles:
        if MIN_RADIUS <= radius <= MAX_RADIUS:
            candidates.append((x, y, radius))
    if not candidates:
        return None, candidates
    return max(candidates, key=lambda item: item[2]), candidates


def same_circle(previous, current):
    """判断相邻帧的两个圆是否属于同一个目标。"""
    if previous is None or current is None:
        return False
    dx = previous[0] - current[0]
    dy = previous[1] - current[1]
    return (
        dx * dx + dy * dy <= TRACK_CENTER_DELTA * TRACK_CENTER_DELTA
        and abs(previous[2] - current[2]) <= TRACK_RADIUS_DELTA
    )


def draw_raw_candidates(image, circles):
    """用灰色细圈显示 CV Lite 的所有候选圆，便于现场排查。"""
    for x, y, radius in circles:
        image.draw_circle(x, y, radius, color=(100, 100, 100), thickness=1)


def draw_main_circle(image, circle, stable_count):
    """显示筛选后的主圆和连续帧稳定状态。"""
    x, y, radius = circle
    state = "STABLE" if stable_count >= STABLE_FRAMES else "CHECK"
    image.draw_circle(x, y, radius, color=(40, 167, 225), thickness=3)
    image.draw_cross(x, y, color=(255, 0, 0), size=10)
    image.draw_string_advanced(
        max(0, x - radius),
        max(0, y - radius - 22),
        16,
        "CIRCLE %s r=%d" % (state, radius),
        color=(40, 167, 225),
    )


def main():
    """运行 CV Lite 圆检测并保留稳定的主目标。"""
    sensor = None
    previous_circle = None
    stable_count = 0
    frame_count = 0

    try:
        # 对齐亚博已验证的 CV Lite 相机链路，避免预览画面比例异常。
        sensor = Sensor(id=2, width=1280, height=960, fps=90)
        sensor.reset()
        sensor.set_framesize(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        sensor.set_pixformat(Sensor.RGB888)

        Display.init(
            Display.ST7701,
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            to_ide=True,
            quality=100,
        )
        MediaManager.init()
        sensor.run()

        clock = time.clock()
        while True:
            clock.tick()
            os.exitpoint()
            image = sensor.snapshot()
            frame_count += 1

            raw_values = cv_lite.rgb888_find_circles(
                CIRCLE_IMAGE_SHAPE,
                image.to_numpy_ref(),
                HOUGH_DP,
                MIN_CENTER_DISTANCE,
                CANNY_HIGH_THRESHOLD,
                ACCUMULATOR_THRESHOLD,
                MIN_RADIUS,
                MAX_RADIUS,
            )
            raw_circles = circle_tuples(raw_values)
            current_circle, candidates = select_main_circle(raw_circles)
            draw_raw_candidates(image, raw_circles)

            if current_circle is None:
                previous_circle = None
                stable_count = 0
                result_text = "raw=%d filtered=0" % len(raw_circles)
            else:
                stable_count = stable_count + 1 if same_circle(previous_circle, current_circle) else 1
                previous_circle = current_circle
                draw_main_circle(image, current_circle, stable_count)
                result_text = "raw=%d valid=%d center=(%d,%d) r=%d stable=%d" % (
                    len(raw_circles),
                    len(candidates),
                    current_circle[0],
                    current_circle[1],
                    current_circle[2],
                    stable_count,
                )

            image.draw_string_advanced(0, 0, 16, "FPS: %.1f" % clock.fps(), color=(255, 255, 255))
            image.draw_string_advanced(
                0,
                18,
                14,
                "raw=%d valid=%d p2=%d" % (len(raw_circles), len(candidates), ACCUMULATOR_THRESHOLD),
                color=(255, 255, 0),
            )
            Display.show_image(image)

            if frame_count % PRINT_PERIOD_FRAMES == 0:
                print("frame=%d %s" % (frame_count, result_text))
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("circle error: %s" % error)
    finally:
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
