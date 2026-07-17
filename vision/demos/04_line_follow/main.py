"""第 4 模块：亚博 K230 单文件视觉巡线示例。

本程序仅输出视觉测量结果，不在 K230 上计算 PID 或直接控制电机。
error 的约定：黑线中心在画面右侧为正，左侧为负；丢线时 valid=0。
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

# 亚博黑线示例的初始 LAB 值。必须以实际胶带和现场灯光重新标定。
BLACK_LINE_THRESHOLD = (21, 33, -15, 9, -9, 6)
MIN_PIXELS = 80
MIN_AREA = 120

# ROI 格式：x, y, w, h, 权重。下方区域离车最近，权重最高。
ROIS = (
    (0, 370, 640, 55, 0.60),
    (0, 300, 640, 45, 0.30),
    (0, 245, 640, 35, 0.10),
)
MIN_VALID_ROIS = 1
PRINT_PERIOD_FRAMES = 10


def largest_line_blob(image, roi):
    """在一条 ROI 内找黑线的最大连通区域；无候选时返回 None。"""
    x, y, width, height, weight = roi
    blobs = image.find_blobs(
        [BLACK_LINE_THRESHOLD],
        roi=(x, y, width, height),
        pixels_threshold=MIN_PIXELS,
        area_threshold=MIN_AREA,
        merge=True,
    )
    if not blobs:
        return None
    return max(blobs, key=lambda blob: blob.pixels())


def measure_line(image):
    """汇总多条 ROI 的线中心，返回 valid、error、用于显示的候选列表。"""
    weighted_x = 0.0
    weight_sum = 0.0
    detections = []

    for roi in ROIS:
        blob = largest_line_blob(image, roi)
        if blob is None:
            continue
        weight = roi[4]
        weighted_x += blob.cx() * weight
        weight_sum += weight
        detections.append((roi, blob))

    if len(detections) < MIN_VALID_ROIS:
        return False, 0, detections

    line_x = int(weighted_x / weight_sum)
    # 约定：线在右侧 -> 正误差，线在左侧 -> 负误差。
    error = line_x - FRAME_WIDTH // 2
    return True, error, detections


def draw_debug(image, valid, error, detections, fps):
    """绘制 ROI、候选线块、综合中心和丢线状态。"""
    for roi in ROIS:
        image.draw_rectangle(roi[0], roi[1], roi[2], roi[3], color=(80, 80, 80), thickness=1)

    for roi, blob in detections:
        image.draw_rectangle(blob.rect(), color=(0, 255, 0), thickness=2)
        image.draw_cross(blob.cx(), blob.cy(), color=(0, 255, 0), size=7)

    center_x = FRAME_WIDTH // 2
    image.draw_line(center_x, 0, center_x, FRAME_HEIGHT, color=(255, 255, 0), thickness=1)
    if valid:
        line_x = center_x + error
        image.draw_line(line_x, ROIS[-1][1], line_x, FRAME_HEIGHT, color=(255, 0, 0), thickness=2)
        text = "LINE valid error=%d" % error
        color = (0, 255, 0)
    else:
        text = "LINE LOST"
        color = (255, 0, 0)
    image.draw_string_advanced(0, 0, 20, text, color=color)
    image.draw_string_advanced(0, 24, 16, "FPS: %.1f" % fps, color=(255, 255, 255))


def main():
    """初始化相机，持续测量巡线误差；本阶段不发送 UART 数据。"""
    sensor = None

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

            valid, error, detections = measure_line(image)
            draw_debug(image, valid, error, detections, clock.fps())
            Display.show_image(image)

            if frame_count % PRINT_PERIOD_FRAMES == 0:
                print("valid=%d error=%d rois=%d" % (1 if valid else 0, error, len(detections)))
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("line follow error: %s" % error)
    finally:
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
