# MSPM0 工具链 / SDK / 库 / 烧录器

> 给 setup-env 用：MSPM0 一套开发环境从装到能烧。核心是 **MSPM0 SDK（DriverLib）+ SysConfig + (CCS Theia 或 Keil) + XDS110/CMSIS-DAP**。

## 一图流（怎么搭起来）

```
SysConfig(图形配引脚/时钟/外设, 自动冲突检测)
        │  生成 ti_msp_dl_config.[ch]
        ▼
MSPM0 SDK / DriverLib (DL_ 前缀驱动层, 类 HAL)
        │  编译 (TI Arm-Clang / GCC / Keil ARMCC)
        ▼
CCS Theia 或 Keil MDK (IDE + 调试)
        │  下载
        ▼
XDS110 (LaunchPad 板载) / CMSIS-DAP (立创板) → 目标芯片
```

## 1. MSPM0 SDK（核心，必装）

- 含 **DriverLib 源码** + 海量例程 + 文档 + SysConfig 集成。下载：ti.com 搜 "MSPM0-SDK"，或随 CCS 安装。
- **DriverLib**：寄存器之上的驱动层，函数前缀 **`DL_`**（如 `DL_GPIO_setPins`、`DL_TimerA_startCounter`、`DL_UART_Main_transmitData`、`DL_ADC12_startConversion`、`DL_MathACL_*`），风格接近 STM32 HAL，比直接撸寄存器友好。
- 支持编译器：**TI Arm-Clang / Arm GCC / IAR / Keil(ARMCC)**。
- **起手务必"导入例程"而非建空工程**。关键例程：
  - `empty`：最小骨架（仅链接 DriverLib 库）。
  - **`empty_driverlib_src`**：把 DriverLib 源码整份拷进工程，可改驱动、自包含——电赛推荐，方便定位问题。
  - 各外设 demo：`gpio_*`、`timer_*`（含 QEI/PWM）、`uart_*`（含 DMA/echo）、`adc12_*`、`mathacl_*`、`iqmath_*` 等，照抄改最快。

## 2. SysConfig（图形化配置，强烈全程用）

- 等价于 STM32CubeMX：图形化配 **引脚 / 外设实例 / 时钟树 / 中断**，**自动检测引脚复用冲突**（电控最易错处，见 04）。
- 形态：CCS/Theia 内置；Keil/IAR 需装 **standalone SysConfig**；也可云端 **dev.ti.com/sysconfig** 直接在浏览器用。
- 产物：`*.syscfg` 配置 + 自动生成 `ti_msp_dl_config.h/.c`（含各外设 init、引脚 PINCM 设置），main 里调 `SYSCFG_DL_init()` 即可。
- **务必把主频从默认 32MHz 拉到 80MHz**（在 SysConfig 的 SYSCTL/时钟模块里设 PLL）。

## 3. IDE 选择

| IDE | 说明 | 建议 |
|---|---|---|
| **CCS Theia**（VS Code 内核，CCS 12.7+/Theia） | TI 官方主推，内置 SysConfig + 调试器，免额外配置 | **新生态首选**，一体化最省心 |
| **Keil MDK 5.38+** | 从 MSPM0 SDK 导入工程，首次需 Pack/初始化；国内最熟 | 有 STM32 Keil 习惯者过渡最顺，配 standalone SysConfig |
| **CCS v12（Eclipse）** | 旧版 Eclipse 内核 | 老用户，新项目优先 Theia |
| **IAR** | 需单独装 SysConfig | 不推荐新手 |
| **VSCode + GCC + FreeRTOS/RT-Thread** | 社区模板（见 github danshoujieyi/TI-MSPM0G3507） | 想上 RTOS / 脱离 Keil 的进阶玩法 |

## 4. 烧录 / 调试器

| 调试器 | 来源 | 用法 |
|---|---|---|
| **XDS110** | TI LaunchPad **板载** | CCS 直连；Keil 里 Debug 选 **CMSIS-DAP**，会多出两个带 "XDS110" 字样的 COM 口（其一可作串口） |
| **CMSIS-DAP** | 立创天猛星/地猛星 **板载 DAP** | 通用，Keil/CCS 都认 |
| **ST-Link / J-Link** | 第三方 | 也可烧 MSPM0（Keil 选对应调试器） |
| **UniFlash** | TI 官方独立烧录工具 | 量产/脱机烧写 hex/out |
| **BSL（板载 Bootloader）** | 芯片自带 | UART/I2C 串口下载，无需调试器（应急） |

## 5. 常用辅助库

- **IQMath / QMath**：定点数学库，把浮点算法平滑移植成定点，可挂 **MATHACL** 硬件加速——MSPM0 无 FPU 时的 PID/解算利器。
- **DSPLib / 控制套件**：滤波、控制相关。
- **printf 重定向**：把 `fputc`/底层 IO 重定向到一路 UART，配合 VOFA+/JustFloat 调 PID（见 04）。

## 参考链接

- [MSPM0G1X0X_G3X0X DriverLib API 指南（TI 官方）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/latest/docs/english/driverlib/mspm0g1x0x_g3x0x_api_guide/html/index.html)
- [MSPM0 SDK Examples Guide（TI 官方）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/1_20_01_06/docs/english/sdk_users_guide/doc_guide/doc_guide-srcs/examples_guide.html)
- [将 SysConfig 与 MSPM0 配合使用（TI 官方·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/1_10_01_05/docs/chinese/tools/sysconfig_guide/doc_guide/doc_guide-srcs/sysconfig_guide_CN.html)
- [CCS Theia IDE 指南（TI 官方·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/1_20_01_06/docs/chinese/tools/ccs_theia_ide_guide/doc_guide/doc_guide-srcs/ccs_theia_ide_guide_CN.html)
- [适用于 MSPM0 的 Keil MDK IDE 指南（TI 官方·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/latest/docs/chinese/tools/keil_ide_guide/doc_guide/doc_guide-srcs/keil_ide_guide_CN.html)
- [MSPM0 IQMath 用户指南（TI 官方·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/1_10_01_05/docs/chinese/middleware/iqmath/doc_guide/doc_guide-srcs/Users_Guide_CN.html)
- [SysConfig 云端在线工具](https://dev.ti.com/sysconfig)
- [MSPM0G3507 开发环境搭建（SysConfig+Keil）（CSDN）](https://blog.csdn.net/2401_88020953/article/details/149455704)
- [Keil 编程 MSPM0G3507 多种调试器烧录（CSDN）](https://blog.csdn.net/weixin_41784968/article/details/147376846)
