"""第 0 模块：可直接由 CanMV IDE 运行的单文件 K230 基础诊断。

此文件刻意不导入本仓库的 core/ 或 protocol.py。IDE 通常只下发当前脚本，
单文件版本可先验证板载摄像头、屏幕与亚博 UART；完整任务程序再使用公共库。
"""

import gc
import os
import time

from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager
from ybUtils.YbUart import YbUart


FRAME_WIDTH = 640
FRAME_HEIGHT = 480
UART_BAUD = 115200
HANDSHAKE_TOKEN = 0x23
HANDSHAKE_PERIOD_FRAMES = 30
AIM_STATUS_PERIOD_FRAMES = 3


def build_frame(function, payload):
    """按团队协议生成 AA 55 LEN FUNC PAYLOAD CHECKSUM 0D 二进制帧。"""
    length = len(payload) + 1
    checksum = (length + function) & 0xFF
    for value in payload:
        checksum = (checksum + value) & 0xFF
    return b"\xAA\x55" + bytes((length, function)) + payload + bytes((checksum, 0x0D))


def send_online_status(uart):
    """发送在线但未识别目标的 AIM_OFFSET 帧，不会驱动主控执行机构。"""
    uart.send(build_frame(0x05, b"\x00\x00\x00\x00\x00"))


def draw_status(image, fps, frame_count):
    """画出阶段、帧率与光轴中心，作为图像链路正常的直观证据。"""
    image.draw_string_advanced(0, 0, 24, "K230 foundation", color=(0, 255, 0))
    image.draw_string_advanced(0, 28, 20, "FPS: %.1f" % fps, color=(255, 255, 255))
    image.draw_cross(FRAME_WIDTH // 2, FRAME_HEIGHT // 2, color=(255, 0, 0), size=12)
    image.draw_string_advanced(0, 52, 16, "frame: %d" % frame_count, color=(255, 255, 0))


def main():
    """初始化板载资源，持续取图显示，并周期发送协议状态帧。"""
    sensor = None
    uart = None

    try:
        uart = YbUart(baudrate=UART_BAUD)

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
            draw_status(image, clock.fps(), frame_count)

            if frame_count % HANDSHAKE_PERIOD_FRAMES == 0:
                uart.send(build_frame(0x04, bytes((HANDSHAKE_TOKEN,))))
            if frame_count % AIM_STATUS_PERIOD_FRAMES == 0:
                send_online_status(uart)

            Display.show_image(image)
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("foundation error: %s" % error)
    finally:
        if uart is not None:
            uart.deinit()
        if sensor is not None:
            sensor.stop()
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()


main()
