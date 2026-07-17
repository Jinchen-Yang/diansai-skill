"""第 3 模块：亚博 K230 单文件圆形检测示例。

使用 CanMV 图像对象的 find_circles() 查找圆形边缘。此阶段独立运行，
不依赖主控串口；连续帧判断会确认检测到的是同一个圆而不是任意候选。
"""

import gc
import os
import time

from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager


# ============================= 现场标定配置区 =============================
FRAME_WIDTH = 400
FRAME_HEIGHT = 240
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

# 更高会减少候选圆，假圆多时提高；真实圆漏检时再降低。
CIRCLE_THRESHOLD = 3500
# 初学调试阶段故意放宽半径范围，先确认底层能不能找到圆，再针对题目收紧。
MIN_RADIUS = 5
MAX_RADIUS = 200

# 同一目标在相邻帧可允许的中心位移和半径变化。
TRACK_CENTER_DELTA = 18
TRACK_RADIUS_DELTA = 10
STABLE_FRAMES = 3
PRINT_PERIOD_FRAMES = 15


def circle_values(circle):
    """将 CanMV 圆对象统一转换为 x、y、r 三个整数。"""
    x, y, radius = circle.circle()
    return int(x), int(y), int(radius)


def select_main_circle(circles):
    """过滤不符合半径范围的候选，返回主圆与过滤后候选列表。"""
    candidates = []
    for circle in circles:
        x, y, radius = circle_values(circle)
        if MIN_RADIUS <= radius <= MAX_RADIUS:
            candidates.append((x, y, radius))
    if not candidates:
        return None, candidates
    return max(candidates, key=lambda item: item[2]), candidates


def same_circle(previous, current):
    """判断两帧主圆是否属于同一目标，防止稳定计数被候选圆跳变污染。"""
    if previous is None or current is None:
        return False
    dx = previous[0] - current[0]
    dy = previous[1] - current[1]
    return (
        dx * dx + dy * dy <= TRACK_CENTER_DELTA * TRACK_CENTER_DELTA
        and abs(previous[2] - current[2]) <= TRACK_RADIUS_DELTA
    )


def draw_circle_result(image, circle, stable_count):
    """画圆、圆心与稳定状态，调试时应观察圆是否贴合真实边缘。"""
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


def draw_raw_candidates(image, circles):
    """用灰色细圈标出底层 find_circles 的所有结果，便于诊断筛选问题。"""
    for circle in circles:
        x, y, radius = circle_values(circle)
        image.draw_circle(x, y, radius, color=(100, 100, 100), thickness=1)


def main():
    """初始化相机，检测最大候选圆并用帧间一致性确认主目标。"""
    sensor = None
    previous_circle = None
    stable_count = 0

    try:
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        sensor.set_pixformat(Sensor.RGB565)

        Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
        MediaManager.init()
        sensor.run()

        clock = time.clock()
        frame_count = 0
        display_x = (DISPLAY_WIDTH - FRAME_WIDTH) // 2
        display_y = (DISPLAY_HEIGHT - FRAME_HEIGHT) // 2

        while True:
            clock.tick()
            os.exitpoint()
            image = sensor.snapshot()
            frame_count += 1

            raw_circles = image.find_circles(threshold=CIRCLE_THRESHOLD)
            current_circle, candidates = select_main_circle(raw_circles)
            draw_raw_candidates(image, raw_circles)
            if current_circle is None:
                previous_circle = None
                stable_count = 0
                result_text = "raw=%d filtered=0" % len(raw_circles)
            else:
                stable_count = stable_count + 1 if same_circle(previous_circle, current_circle) else 1
                previous_circle = current_circle
                draw_circle_result(image, current_circle, stable_count)
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
                "raw=%d valid=%d threshold=%d" % (len(raw_circles), len(candidates), CIRCLE_THRESHOLD),
                color=(255, 255, 0),
            )
            Display.show_image(image, x=display_x, y=display_y)
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
