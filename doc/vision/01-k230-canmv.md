# K230 / CanMV 详解（电赛视觉主力平台）

> 面向 NUEDC 小车：K230 当"视觉协处理器"，MSPM0/STM32 做实时电控，串口把结果喂给主控。
> 本篇讲**芯片定位 + 开发板 + CanMV 固件 + 从零上手流程**。视觉任务怎么写见 `02-k230-vision-tasks.md`，串口通信见 `03-uart-to-mcu.md`。

## 一、芯片定位：嘉楠 Kendryte K230

K230 是嘉楠科技（Canaan / 勘智 Kendryte）2023 年发布的边缘 AIoT SoC，是 K210 的换代产品。

| 模块 | 规格 | 工程含义 |
|---|---|---|
| CPU | **双核玄铁 C908 RISC-V**：大核 1.6GHz（带 RVV1.0 矢量扩展）+ 小核 0.8GHz | 大核跑 CanMV/MicroPython 应用，小核跑实时/调试 shell |
| AI 加速 | 第三代自研 **KPU**（Knowledge Process Unit），**6 TOPS 等效算力**（INT8/INT16） | 推理性能约 K210 的 13.7 倍，可跑 YOLOv8n / YOLO11n |
| 内存 | LPDDR4，1GB / 2GB（部分模组板 512MB LPDDR3） | 跑检测/分割模型够用 |
| 摄像头 | **3 路 MIPI-CSI**，最大支持 4K；常配 GC2093（200 万像素）/ OV5647 | 多路输入，画质优于 K210 的 OV2640 |
| 显示 | MIPI-DSI（最高 1080p）+ HDMI（最高 1080p）；多数开发板带 3.5" LCD | 现场不接电脑也能看画面/调阈值 |
| 启动 | 百毫秒级快启；整板典型功耗 < 2W | 电赛上电即用，掉电重启不慌 |
| 其它外设 | 2.4G WiFi、USB2.0、UART/I2C/PWM/SPI、树莓派兼容 40Pin GPIO | 原生 UART 直连单片机，电赛友好 |

> CPU 综合算力约为 K210 的 8.5 倍，KPU 约 13.7 倍。

**与 K210 的关键差异（避坑）**：CanMV-K230 的 MicroPython API 与 K210 **不兼容**——摄像头改用 `media.sensor`、串口引脚改用 `FPIOA` 复用方式、显示改用 `media.display`。**抄 K210 代码会直接报错**，务必照 K230 文档。

## 二、开发板：CanMV-K230 家族

CanMV = Canaan 的 MicroPython 视觉运行环境（对标 OpenMV）。常见板子：

| 开发板 | 特点 | 大致价格 |
|---|---|---|
| **嘉楠官方 CanMV-K230** | 双 Type-C、3 路 CSI、HDMI、官方首发板 | 首发约 249 元 |
| **立创·庐山派 K230**（LCKFB） | 板载 3.5" LCD + GC2093 + GH1.25 串口座、文档/例程最全、社区活跃 | ~130–230 元 |
| **01Studio CanMV-K230** | 带屏、教程体系完善 | ~200+ 元 |
| **CanMV-K230D-Zero** | 邮票孔核心板形态，体积小 | ~100+ 元 |

**电赛建议**：选**立创庐山派**或**01Studio**带屏版——板载 LCD 能现场调阈值、串口座子接线方便、中文文档+例程最丰富。下文引脚以庐山派为例。

## 三、CanMV 固件 = 基于 MicroPython

CanMV 固件把 MicroPython 解释器 + 机器视觉库（移植自 OpenMV）+ KPU AI 库打包，烧进 SD 卡。你写 `.py`，板子直接解释执行，无需编译——这是上手快的核心原因。三类 API：

- **`machine`**：底层外设（UART / I2C / SPI / PWM / FPIOA / Pin / Timer），同 MicroPython 习惯。
- **`media.*`**：`sensor`（摄像头）、`display`（显示）、`media`（缓冲管理）——K230 特有。
- **机器视觉 `img.*`**：`find_blobs / get_regression / find_apriltags / find_qrcodes` 等，沿用 OpenMV 函数名。
- **AI / KPU**：`nncase_runtime`、`ulab`（类 numpy）、官方 `YOLO` 模块等，部署 kmodel 模型。

官方文档（最权威，务必以它为准）：
- 嘉楠 CanMV-K230 文档：`https://www.kendryte.com/k230_canmv/zh/main/`
- 嘉楠开发者社区镜像：`https://developer.canaan-creative.com/k230_canmv/`

## 四、从零上手流程（5 步）

### 1. 下载并烧录固件
- 到嘉楠资源页 `https://developer.canaan-creative.com/resource` 下载 `CanMV-K230_micropython_*.img.gz`。
- 解压得 `sysimage-sdcard.img`，用 **balenaEtcher / Rufus**（Win）或 `dd`（Linux/Mac）写入 **TF/SD 卡**。
- 卡插回板子。注意区分模组型号（1G/2G、是否带屏），固件要对应板子。

### 2. 连接与识别
- 板子有两个 Type-C：一个供电+下载，一个是 **REPL 串口**（CanMV IDE 连这个）。
- 连上电脑后会出现一个名为 **CanMV 的虚拟 U 盘** + 一个虚拟串口。

### 3. CanMV IDE（基于 OpenMV IDE）
- 下载最新 CanMV IDE（Win 当前 4.0x 版）：`https://developer.canaan-creative.com/resource`。
- 左下角 **connect（连接）** → 选板子串口 → 点 **绿色三角运行** 当前脚本。
- 自带阈值编辑器、帧缓冲查看、串口终端——电赛调色块/巡线阈值全靠它。

### 4. MicroPython 开发模式
- **在线调试**：IDE 里写脚本点运行，改完即跑，适合调参。
- **离线自启**：把脚本命名为 **`main.py`** 放进 CanMV 虚拟盘（或 `/sdcard/`），板子上电自动执行——**电赛上车必须这样**（脱离电脑独立运行）。

### 5. 一个最小可运行骨架
```python
import time
from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager

sensor = Sensor(width=320, height=240)        # 低分辨率=高帧率，循迹够用
sensor.reset()
sensor.set_framesize(width=320, height=240)
sensor.set_pixformat(Sensor.RGB565)           # 彩色；巡线可 GRAYSCALE
Display.init(Display.ST7701, to_ide=True)      # 板载 LCD + IDE 同时回显
MediaManager.init()
sensor.run()

clock = time.clock()
while True:
    clock.tick()
    img = sensor.snapshot()                    # 取一帧
    # === 这里做视觉处理（见 02 篇）===
    Display.show_image(img)
    print(clock.fps())                         # 看帧率
```

## 五、AI / KPU 模型部署入口

- **模型格式**：K230 跑的是 **kmodel**。流程 `.pt → ONNX → kmodel`，用嘉楠 **nncase** 转换工具。**nncase 版本必须与板卡固件版本严格匹配**，否则模型加载失败。
- **零代码训练**：嘉楠 **AICube** 在线平台，上传数据集训练并一键导出 kmodel，适合不会训模型的队友。
- **现成 YOLO**：CanMV 提供 `YOLO` 模块，支持 **YOLOv5 / YOLOv8 / YOLO11** 的分类/检测/分割。电赛推荐 **YOLOv8n（nano）**——v8s 在 K230 上易掉帧。
- 详见 `02-k230-vision-tasks.md` 第五节。

## 关键要点（速记）

- K230 = 双核 C908 RISC-V（大核1.6G+小核0.8G）+ 6TOPS KPU，K210 换代，**API 不兼容 K210**。
- CanMV 固件 = MicroPython + OpenMV 视觉库 + KPU；写 `.py` 即跑，不编译。
- 上手：烧 SD 卡固件 → CanMV IDE 连 REPL 串口调试 → 上车把脚本存成 `main.py` 自启。
- 摄像头用 `media.sensor`，显示用 `media.display`，外设用 `machine`，视觉用 `img.*`（同 OpenMV）。
- 模型走 kmodel，nncase 转换且版本须配固件；不会训模型用 AICube 零代码；检测优先 YOLOv8n。
- 电赛选带屏的庐山派/01Studio，现场调阈值+串口座方便；价格约 130–230 元。

## 参考链接

- CanMV-K230 官方文档（主）: https://www.kendryte.com/k230_canmv/zh/main/
- 嘉楠开发者社区 K230 文档: https://developer.canaan-creative.com/k230_canmv/
- CanMV-K230 快速入门指南: https://www.kendryte.com/k230_canmv/zh/v1.5/quick_start.html
- 烧录固件官方教程: https://www.kendryte.com/k230_canmv/main/zh/userguide/how_to_burn_firmware.html
- 嘉楠资源下载页（固件 + CanMV IDE）: https://developer.canaan-creative.com/resource
- CanMV-K230D-Zero 开发板: https://www.kendryte.com/k230_canmv/zh/main/userguide/boards/canmv_k230d.html
- 立创·庐山派 K230 文档中心: https://wiki.lckfb.com/zh-hans/lushan-pi-k230/
- 庐山派 K230 简介（参数）: https://wiki.lckfb.com/zh-hans/lushan-pi-k230/open-source-hardware/profile.html
- 庐山派 K230 快速上手: https://wiki.lckfb.com/zh-hans/lushan-pi-k230/quick-start.html
- 01Studio CanMV-K230 文档: https://wiki.01studio.cc/en/docs/canmv_k230/
- 嘉楠 249 元发布 CanMV-K230（IT之家）: https://www.ithome.com/0/725/728.htm
- 嘉楠 AICube 在线训练平台 / nncase（GitHub）: https://github.com/kendryte/nncase
