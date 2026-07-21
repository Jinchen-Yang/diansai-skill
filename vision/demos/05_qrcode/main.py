"""第 5 模块：亚博 K230 单文件二维码识别示例。

本阶段只完成二维码的定位与内容读取，不依赖 UART 或主控工程。
CanMV IDE 只需打开并运行本文件。
"""

import gc
import os
import time

from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager


# ============================= 现场配置区 =============================
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
PRINT_PERIOD_FRAMES = 30
MAX_PAYLOAD_CHARS = 20


def center_from_rect(rect):
    """把二维码矩形 (x, y, w, h) 转换为中心坐标。"""
    x, y, width, height = rect
    return x + width // 2, y + height // 2


def payload_preview(payload):
    """截断长内容，保证屏幕叠字不会遮住整个预览画面。"""
    if len(payload) <= MAX_PAYLOAD_CHARS:
        return payload
    return payload[:MAX_PAYLOAD_CHARS - 3] + "..."


def draw_qrcode(image, index, qrcode):
    """绘制二维码外框、中心与编号，并返回可供串口层使用的结果。"""
    rect = qrcode.rect()
    payload = qrcode.payload()
    center_x, center_y = center_from_rect(rect)
    x, y, width, height = rect

    image.draw_rectangle(rect, color=(0, 255, 0), thickness=3)
    image.draw_cross(center_x, center_y, color=(255, 0, 0), size=10)
    image.draw_string_advanced(
        x,
        max(0, y - 20),
        16,
        "QR%d %s" % (index, payload_preview(payload)),
        color=(0, 255, 0),
    )
    return (payload, center_x, center_y, width, height)


def main():
    """运行二维码检测、画面显示和低频调试输出。"""
    sensor = None
    last_payloads = None
    frame_count = 0

    try:
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        sensor.set_pixformat(Sensor.RGB565)

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
            image = sensor.snapshot()
            frame_count += 1

            qrcodes = image.find_qrcodes()
            results = []
            for index, qrcode in enumerate(qrcodes, start=1):
                results.append(draw_qrcode(image, index, qrcode))

            payloads = tuple(item[0] for item in results)
            image.draw_string_advanced(
                0,
                0,
                18,
                "QR=%d FPS: %.1f" % (len(results), clock.fps()),
                color=(255, 255, 0),
            )
            Display.show_image(image)

            if payloads != last_payloads or frame_count % PRINT_PERIOD_FRAMES == 0:
                print("qrcode count=%d payloads=%s" % (len(results), payloads))
                last_payloads = payloads
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("qrcode error: %s" % error)
    finally:
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
