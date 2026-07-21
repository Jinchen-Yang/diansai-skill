# K230 Vision Library

面向亚博智能 K230、CanMV IDE for K230 v4.0.7 的电赛视觉代码库。库的目标是让传统视觉、模型推理与串口回传使用同一套相机、配置和协议接口。

## 使用顺序

1. 先完成 `docs/00_foundation.md` 的原厂教程和上板自检。
2. 将本目录的内容复制到 K230 SD 卡的同一目录，并把 `main.py` 作为启动文件运行。
3. 屏幕与 IDE 能看到实时画面、左上角 FPS，并每秒发送一次握手帧，即完成第 0 模块。
4. 后续模块会在本目录继续增加；每个模块的文档开头都先写明需要学习的亚博教程。

## 目录

```text
vision/
  core/             相机显示、UART 链路、公共配置
  docs/             学习顺序、接线与调参说明
  demos/            每项能力的独立示例，可直接由 CanMV IDE 运行
  models/           KPU/YOLO 模型与类别清单（后续加入）
  tasks/            按赛题组合的任务程序（后续加入）
  protocol.py       从 ../contracts/protocol.yaml 自动生成，勿手改
  main.py           当前阶段的基础相机和 UART 诊断程序
```

## 串口约定

K230 与主控使用 3.3V TTL UART、115200 8N1、TX/RX 交叉且必须共地。帧定义只来自 `../contracts/protocol.yaml`；修改协议后，lead 运行 `tools/gen_protocol.py`，再把生成的 `protocol.py` 同步到本目录。

## 当前阶段

第 0 模块只验证相机、屏幕、FPIOA/UART 和二进制握手帧。它不包含色块、巡线或模型算法。

## 文档约定

每个视觉模块文档都必须有“现场标定参数（比赛时必看）”一节，清楚记录参数含义、调整时机和调试顺序。

## 命名约定

当使用 CanMV 的 `image` 模块时，`image` 只能表示该模块，不得作为当前帧变量名。相机快照统一命名为 `frame`，例如 `frame = sensor.snapshot()`。这避免 `image.Image(...)` 被当前帧对象遮蔽。
