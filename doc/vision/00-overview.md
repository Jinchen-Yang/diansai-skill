# 电赛嵌入式视觉方案总览与选型

> 给 NUEDC 小车队：一句话选型 + 主流方案横向对比。本队默认走 **K230（CanMV）** 路线（详见 `01`/`02`/`03`）。

## 一、两类视觉方案（先分清）

- **MCU 级智能相机**（K230 / OpenMV / ESP32-CAM）：无操作系统或轻量运行时，**上电即跑、原生 UART 直连主控、掉电不怕、功耗低**。电赛主力。
- **嵌入式 Linux 上位机**（树莓派 / Jetson）：跑完整 Linux+OpenCV/CUDA，**算力强但启动慢（25–30s）、掉电易损 SD 卡、串口需配置、功耗高（数瓦~25W）**。仅特定赛题值得。

## 二、选型口诀

- 巡线 / 色块 / AprilTag / 二维码 / 简单数字 → **K230 或 OpenMV**（开机即跑、串口直连、阈值好标定）。
- 必须深度学习目标检测/分类 → **K230（6T KPU 跑 YOLOv8n）** 优先；超大模型才上 **Jetson**。
- 复杂传统 CV 算法链且能接受 Linux → **树莓派 4B/5**（处理好掉电与串口）。
- 极致省钱 / WiFi 图传 → **ESP32-CAM / XIAO ESP32S3 Sense**（不做实时主视觉）。

## 三、横向对比表

| 方案 | 算力 | 价格(RMB) | 上手难度 | 启动速度 | 串口直连MCU | AI能力 | 电赛适配结论 |
|---|---|---|---|---|---|---|---|
| **K230 (CanMV)** | 强(C908 1.6G + **6T KPU**) | **¥130–250** | ★易(MicroPython+IDE) | **百毫秒级** | ✅原生UART1/2/4 | **强**(YOLOv8n/v5s) | **首选**：算力/价/启动/串口全优 |
| **OpenMV H7/Plus/RT1062** | 中(MCU级, QVGA 25–50FPS) | ¥700–900 | ★易(同上) | **即时(无OS)** | ✅原生UART1 | 弱(小型TF模型) | 任务简单/预算够可选，生态最成熟 |
| **ESP32-CAM** | 弱(520KB RAM) | **¥20–40** | ★★★难(自写CV) | 即时 | ⚠引脚紧张 | 弱(ESP-WHO) | 备选/图传，做主视觉吃力 |
| **XIAO ESP32S3 Sense** | 弱–中(8MB PSRAM) | ¥80–110 | ★★★ | 即时 | ⚠引脚少 | 轻量(ESP-DL) | 低成本AI/图传，非主力 |
| **树莓派 4B/5** | 强(传统CV) | ¥357–600 | ★★中(Linux+Py) | **慢(25–30s)** | ⚠需配置(Zero要关蓝牙) | 中(CPU跑NN慢) | 复杂OpenCV赛题，防掉电损卡 |
| **Jetson Orin Nano(Super)** | **极强(40–67 TOPS)** | ¥1800–3000+ | ★★★(JetPack/CUDA) | 慢 | ⚠/dev/ttyTHS需配置 | **强(实时深度学习)** | 仅深度学习重赛题；功耗大、贵 |

> 价格为公开渠道参考价，**以当年主办方配件表为准**。

## 四、各方案要点速记

### K230（CanMV）— 本队主力
6TOPS KPU + 双核 RISC-V，百毫秒快启，原生 UART，约 130–250 元，既能传统 CV（find_blobs/巡线）又能跑 YOLO。MicroPython 开发，CanMV IDE 调阈值。详见 `01-k230-canmv.md`。

### OpenMV — 最直接的同档替代/对照
STM32H7/RT1062 + MicroPython，生态最成熟、IDE 最顺手；`find_blobs / find_apriltags / find_qrcodes / find_lines` 开箱即用，一个脚本里既做视觉又发串口。**算力不足以跑通用大模型**，且比 K230 贵不少。
```python
# OpenMV 色块 + 串口（注意：OpenMV 固定 UART1, TX=P4/RX=P5）
import sensor, image
from machine import UART          # 旧固件: from pyb import UART
sensor.reset(); sensor.set_pixformat(sensor.RGB565); sensor.set_framesize(sensor.QVGA)
sensor.set_auto_gain(False); sensor.set_auto_whitebal(False)   # 颜色识别必关 AGC/AWB
uart = UART(1, 115200, timeout_char=200)
red = [(30,100,15,127,15,127)]
while True:
    img = sensor.snapshot()
    blobs = img.find_blobs(red, pixels_threshold=100, area_threshold=100, merge=True)
    if blobs:
        b = max(blobs, key=lambda x: x.pixels())
        uart.write(bytes([0xAA,0x55, b.cx()&0xFF, b.cy()&0xFF, 0x5B]))  # 实战改用 contracts/protocol
```

### ESP32-CAM / XIAO ESP32S3 Sense
OV2640 摄像头，便宜（20–110 元）、WiFi 图传是强项；但 RAM 紧、**无 find_blobs 之类开箱函数**（要自己 C/Arduino 写 CV），串口引脚易和 Flash/摄像头冲突。S3 Sense 有 8MB PSRAM 可跑 ESP-DL 轻量 AI。**当图传/低成本探索，不当实时主视觉**。

### 树莓派 4B/5 + OpenCV
传统 CV 能力强、Python 生态全，可外接屏调试。硬伤：开机 25–30s、**直接断电易损 SD 卡**（电赛频繁开关电是大坑）、GPIO 串口要配置（`ttyAMA0` 稳/`ttyS0` 受频率影响；带蓝牙机型要先关蓝牙释放 PL011）。仅复杂 OpenCV 算法链场合用。

### Jetson Nano / Orin Nano
CUDA + Tensor Core 实时跑 YOLO/分割，远超其它方案；但贵（1800–3000+）、功耗 7–25W、同样有 Linux 启动慢/掉电/串口配置问题。**普通巡线/色块杀鸡用牛刀**，仅高难度检测赛题上。

## 五、与本仓库的衔接

- 默认路线 K230 → `vision/` lane（算法）用 CanMV 出脚本，收发帧只用 `contracts/protocol.py`（与主控 `protocol.h` 同源）。
- 串口帧协议、引脚以 `contracts/` 为准；选型最终以当年配件表（`inputs/partslist/`）为准。

## 参考链接

- K230 CanMV 官方文档: https://www.kendryte.com/k230_canmv/zh/main/
- OpenMV 官方文档: https://docs.openmv.io/
- OpenMV 例程库(GitHub): https://github.com/openmv/openmv
- OpenMV 中文教程（星瞳）: https://book.openmv.cc/
- XIAO ESP32S3 Sense 摄像头: https://wiki.seeedstudio.com/cn/xiao_esp32s3_camera_usage/
- ESP-WHO / ESP-DL: https://github.com/espressif/esp-who , https://github.com/espressif/esp-dl
- 树莓派官方文档: https://www.raspberrypi.com/documentation/
- OpenCV(GitHub): https://github.com/opencv/opencv
- NVIDIA Jetson Orin: https://developer.nvidia.com/embedded/jetson-orin
- 嘉楠 249 元发布 CanMV-K230(IT之家): https://www.ithome.com/0/725/728.htm
