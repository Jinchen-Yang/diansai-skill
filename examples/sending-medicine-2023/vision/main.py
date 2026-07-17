# K230 视觉主循环（CanMV）—— 取流 → 处理 → 用 protocol 发帧给主控
# 现场标定项集中在 config.py；K230 镜像版本须与队伍锁定一致（见 README.md）。
import time

try:
    import sensor, image            # CanMV 硬件库；主机仅 py_compile 检查语法
    from machine import UART
    _HW = True
except ImportError:
    _HW = False                     # 主机环境无硬件，仅供语法/逻辑检查

import protocol as proto
import config as cfg
import line_follow, blob_track, digit_recog


def init_uart():
    if not _HW:
        return None
    return UART(cfg.UART_ID, cfg.BAUD)


def send(uart, frame):
    if uart:
        uart.write(frame)


def main():
    uart = init_uart()
    if _HW:
        sensor.reset()
        sensor.set_pixformat(sensor.GRAYSCALE)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(time=300)

    send(uart, proto.handshake(0x01))           # 上电握手
    mode = cfg.MODE_LINE

    while True:
        img = sensor.snapshot() if _HW else None
        if mode == cfg.MODE_LINE:
            err = line_follow.line_error(img, cfg)
            if err is not None:
                send(uart, proto.line_error(int(err)))
        elif mode == cfg.MODE_BLOB:
            xy = blob_track.find(img, cfg)
            if xy:
                send(uart, proto.blob_xy(int(xy[0]), int(xy[1])))
        elif mode == cfg.MODE_DIGIT:
            cls = digit_recog.recognize(img, cfg)
            if cls is not None:
                send(uart, proto.target_class(int(cls[0]), int(cls[1])))

        if not _HW:
            break                                # 主机下不进死循环
        time.sleep_ms(10)


if __name__ == "__main__":
    main()
