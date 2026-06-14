# 自动生成 — 勿手改。源: contracts/protocol.yaml  生成器: tools/gen_protocol.py
# K230 <-> 主控 UART 帧协议 (MicroPython / K230 端)
import struct

PROTOCOL_SIG = "bd8385352fff6e42"   # 两端一致性签名，须与 protocol.h 相同
HEADER = bytes((0xaa, 0x55))
TAIL = 0x0d
MAX_DATA = 32
# 链路: 115200 8N1, 3.3V TTL

# 功能码
FUNC_BLOB_XY = 0x01  # 色块/光点中心坐标
FUNC_LINE_ERROR = 0x02  # 巡线中线偏差（喂给 PID）
FUNC_TARGET_CLASS = 0x03  # 目标类别 + 置信度
FUNC_HANDSHAKE = 0x04  # 上电握手 / ACK


def _checksum(length, func, payload):
    s = (length + func) & 0xFF
    for b in payload:
        s = (s + b) & 0xFF
    return s


def build(func, payload=b""):
    """组一帧完整字节串。"""
    length = len(payload) + 1  # +1 = func
    s = _checksum(length, func, payload)
    return HEADER + bytes((length, func)) + payload + bytes((s, TAIL))

def blob_xy(cx, cy):
    """色块/光点中心坐标"""
    return build(FUNC_BLOB_XY, struct.pack("<hh", cx, cy))

def line_error(error):
    """巡线中线偏差（喂给 PID）"""
    return build(FUNC_LINE_ERROR, struct.pack("<h", error))

def target_class(class_id, confidence):
    """目标类别 + 置信度"""
    return build(FUNC_TARGET_CLASS, struct.pack("<BB", class_id, confidence))

def handshake(token):
    """上电握手 / ACK"""
    return build(FUNC_HANDSHAKE, struct.pack("<B", token))


class Parser:
    """逐字节喂入；feed() 返回 (func, data_bytes) 或 None。重同步状态机。"""
    def __init__(self):
        self.st = 0; self.len = 0; self.idx = 0; self.sum = 0; self.buf = bytearray(MAX_DATA)
    def feed(self, c):
        if self.st == 0:   self.st = 1 if c == HEADER[0] else 0
        elif self.st == 1: self.st = 2 if c == HEADER[1] else (1 if c == HEADER[0] else 0)
        elif self.st == 2:
            self.len = c; self.sum = c; self.idx = 0
            self.st = 3 if 0 < c <= MAX_DATA else 0
        elif self.st == 3:
            self.buf[self.idx] = c; self.idx += 1; self.sum = (self.sum + c) & 0xFF
            if self.idx >= self.len: self.st = 4
        elif self.st == 4: self.st = 5 if c == self.sum else 0
        elif self.st == 5:
            self.st = 0
            if c == TAIL:
                return self.buf[0], bytes(self.buf[1:self.len])
        return None
