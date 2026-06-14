# 算法 lane 环境（K230 视觉）

> K230 是独立板，自带电源与摄像头——**几乎全程不依赖小车主电路**，可桌面独立开发调试。
> 版本里 "待核实" 的装好后回填，保证三机一致。

## 安装顺序

1. **CanMV IDE** — 嘉楠 / 立创 CanMV 渠道。K230 MicroPython 开发与在线预览。
2. **K230 固件镜像 (CanMV)** — 嘉楠官方 / 板厂 Wiki。**★ 三人锁定同一个镜像版本**，否则行为不一致。
3. **USB-Serial 驱动** — 板厂提供，用于通信/烧录。
4. **串口助手** — 验 `contracts/protocol.py` 帧与主控对接。

## 自检通过判据

- 板子上电启动进 **CanMV REPL**；IDE 连上能跑摄像头示例（出图）。
- 能 `import` 仓库 `contracts/protocol.py` 并用 `line_error()` / `blob_xy()` 组帧发出（串口助手能看到 `AA 55 ... 0D`）。

## 与契约的关系

- K230 端发帧/收帧**只用 `contracts/protocol.py`**（由 `gen_protocol.py` 生成，和主控端 `protocol.h` 同源同签名）。
- 协议要改 → 找 lead 改 `contracts/protocol.yaml` 重生成，你再 `git pull`，**不要自己在 K230 端硬编帧格式**。
