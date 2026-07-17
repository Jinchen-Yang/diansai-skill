"""亚博 K230 的 UART 链路封装。

使用原厂 YbUart，避免在任务算法中重复处理板级 FPIOA 映射。协议帧由上层
protocol.py 生成，本文件只负责可靠地发送和读取原始字节。
"""

from ybUtils.YbUart import YbUart


class UartLink:
    """与主控相连的单路 3.3V TTL UART。"""

    def __init__(self, baudrate):
        self._uart = YbUart(baudrate=baudrate)

    def send(self, packet):
        """发送 protocol.py 产生的完整二进制帧。"""
        self._uart.send(packet)

    def read(self):
        """非阻塞读取主控返回的数据；没有数据时返回空值。"""
        return self._uart.read()

    def deinit(self):
        """释放串口，供 IDE 停止程序或任务切换时调用。"""
        self._uart.deinit()
