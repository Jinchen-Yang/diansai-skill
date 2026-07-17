"""第 2 模块：亚博 K230 单文件矩形检测示例。

本程序使用 CanMV 图像对象的 find_rects()。它依据边缘和几何形状寻找矩形，
不依赖颜色阈值；直接由 CanMV IDE 运行，不依赖主控或其他本地文件。
"""

import gc
import os
import time

from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager


# ============================= 现场标定配置区 =============================
# 用较低分辨率换取更稳定的帧率；矩形坐标均以这张 400x240 图像为准。
FRAME_WIDTH = 400
FRAME_HEIGHT = 240
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

# find_rects 的边缘响应阈值。背景杂乱、假框多时调高；真实矩形经常漏检时调低。
RECT_THRESHOLD = 8000

# 过滤太小的候选框。它是外接框面积，不代表真实透视下的矩形面积。
MIN_BBOX_AREA = 1200
STABLE_FRAMES = 3
PRINT_PERIOD_FRAMES = 15


def rectangle_area(rectangle):
    """用外接框面积排序，优先选择画面中的主矩形。"""
    x, y, width, height = rectangle.rect()
    return width * height


def select_main_rectangle(rectangles):
    """过滤过小候选框后，返回最大的矩形；无有效候选时返回 None。"""
    candidates = []
    for rectangle in rectangles:
        if rectangle_area(rectangle) >= MIN_BBOX_AREA:
            candidates.append(rectangle)
    if not candidates:
        return None
    return max(candidates, key=rectangle_area)


def draw_rectangle_result(image, rectangle, stable_count):
    """画主矩形、四个角点和中心，辅助判断漏检或误检。"""
    x, y, width, height = rectangle.rect()
    center_x = x + width // 2
    center_y = y + height // 2
    state = "STABLE" if stable_count >= STABLE_FRAMES else "CHECK"

    image.draw_rectangle(rectangle.rect(), color=(40, 167, 225), thickness=3)
    for point in rectangle.corners():
        image.draw_circle(point[0], point[1], 5, color=(255, 255, 0))
    image.draw_cross(center_x, center_y, color=(255, 0, 0), size=10)
    image.draw_string_advanced(
        x,
        max(0, y - 22),
        16,
        "RECT %s (%d,%d)" % (state, center_x, center_y),
        color=(40, 167, 225),
    )
    return center_x, center_y


def main():
    """初始化相机后，逐帧检测、筛选并显示最大的矩形。"""
    sensor = None
    stable_count = 0

    try:
        sensor = Sensor()
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

            rectangle = select_main_rectangle(image.find_rects(threshold=RECT_THRESHOLD))
            if rectangle is None:
                stable_count = 0
                result_text = "no rectangle"
            else:
                stable_count += 1
                center_x, center_y = draw_rectangle_result(image, rectangle, stable_count)
                result_text = "center=(%d,%d) stable=%d" % (center_x, center_y, stable_count)

            image.draw_string_advanced(0, 0, 16, "FPS: %.1f" % clock.fps(), color=(255, 255, 255))
            Display.show_image(image, x=display_x, y=display_y)

            if frame_count % PRINT_PERIOD_FRAMES == 0:
                print("frame=%d %s" % (frame_count, result_text))
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("rectangle error: %s" % error)
    finally:
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
