"""亚博 K230 / CanMV v4.0.7 相机与显示生命周期封装。"""

import gc
import os
import time

from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager


class CameraRuntime:
    """把 Sensor、Display 与 MediaManager 的初始化和释放收在一个地方。"""

    def __init__(self, width, height, show_to_ide=True):
        self._width = width
        self._height = height
        self._show_to_ide = show_to_ide
        self._sensor = None
        self._clock = None

    def start(self):
        """初始化板载摄像头和 ST7701 屏幕，并启动取流。"""
        self._sensor = Sensor()
        self._sensor.reset()
        self._sensor.set_framesize(width=self._width, height=self._height)
        self._sensor.set_pixformat(Sensor.RGB565)

        Display.init(
            Display.ST7701,
            width=self._width,
            height=self._height,
            to_ide=self._show_to_ide,
        )
        MediaManager.init()
        self._sensor.run()
        self._clock = time.clock()

    def snapshot(self):
        """取一帧图像，并推进 FPS 统计。"""
        self._clock.tick()
        os.exitpoint()
        return self._sensor.snapshot()

    def fps(self):
        """返回当前循环的估算帧率。"""
        return self._clock.fps()

    def show(self, image):
        """把叠加了调试图形的图像显示到板载屏幕和 IDE。"""
        Display.show_image(image)

    def service(self):
        """释放本帧临时对象，避免长时间运行出现内存碎片。"""
        gc.collect()

    def stop(self):
        """按 CanMV 推荐顺序关闭相机、显示和媒体缓冲。"""
        if self._sensor is not None:
            self._sensor.stop()
            self._sensor = None
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()
