# 控制 lane 环境（MSPM0G3507 固件）

> 版本里 "待核实" 的，装好后把确切版本回填到本表和 `env/manifest.yaml`，保证三机一致。

## 安装顺序

1. **CCS Theia (Code Composer Studio)** — TI 官网 `ti.com/tool/CCSTUDIO`。主力 IDE。
2. **MSPM0 SDK** — `dev.ti.com` 或 CCS 内 SDK 安装器。提供 DriverLib + 示例。
3. **SysConfig** — 随 CCS/SDK，图形化配引脚/外设，生成 `ti_msp_dl_config.c`。
4. **工具链**（Arm GNU / TI clang）— 随 CCS。
5. **XDS110 驱动** — MSPM0 LaunchPad 板载调试器；随 CCS 安装。
6. **VOFA+** — `vofa.plus`，PID 在线整定（JustFloat 协议，见 KB 08）。
7. **串口助手** — 协议联调用。
8. （备用）Keil MDK — 仅当回退 STM32 时。

## 自检通过判据

- 能新建 MSPM0G3507 工程并**编译出 `.out/.hex`**。
- LaunchPad 板载 XDS110 能**识别 + 烧录 + 调试**。
- VOFA+ 能收到多通道 JustFloat 波形。

## 与契约的关系

- 固件用 `contracts/protocol.h`（由 `tools/gen_protocol.py` 生成）做 K230 收帧——**勿手改，改协议改 `protocol.yaml` 重生成**。
- 引脚以 `contracts/pinmap.yaml` 为准；SysConfig 配置须与之一致（Pass C 的 firmware-scaffold 会据 pinmap 生成 SysConfig 工程）。
