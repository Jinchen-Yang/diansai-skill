# MSPM0G3507 开发板选型 + 现成轮子

> 给 select-parts / setup-env 用：练手/打样板怎么选，社区有哪些现成可抄的工程。

## 开发板对比

| 开发板 | 价格量级 | 调试器 | 资料/亮点 | 适用 |
|---|---|---|---|---|
| **LP-MSPM0G3507**（TI 官方 LaunchPad） | 百元级 | 板载 **XDS110** | 3键2LED(含RGB)、温度+光照传感器、4Msps ADC 外部缓冲、能量测量、BoosterPack 接口；最权威 | 验证官方例程、需要 BoosterPack 扩展 |
| **立创·天猛星 TMX-MSPM0G3507** | 5 片套 ≈ **29.9 元** | 板载 **CMSIS-DAP** | **中文 wiki 最全**：CCS-Theia/Keil 入门 + **PID 入门套件**（编码器电机+TB6612+屏幕曲线）+ PWM/编码器/UART 教程 | **电赛练手首选**，资料/套件齐 |
| **立创·地猛星 DMX-MSPM0G3507** | 单板个位数元 | 板载 DAP | 精简核心板，省空间 | 小车实装主控、便宜 |
| **WeAct MSPM0G3507 核心板** | 低价 | 外接 | 第三方核心板，mixed-signal 定位交叉验证 | 第三方核心板备选 |
| **番茄派 / 其它核心板** | 个位数元 | 外接 | 精简核心板 | 实装省空间 |

> 实战路线：**先用天猛星把 SysConfig + DriverLib + QEI/PWM/UART 三件套跑通**（中文教程多、报错好查），再换地猛星/自制核心板做小车实装。

## 现成好用的东西（例程 / 教程 / 开源工程）

### TI 官方例程（SDK 内）
- `empty` / **`empty_driverlib_src`**：工程骨架起手。
- `timer_*`（QEI、互补PWM+死区）、`uart_*`（DMA/echo/中断）、`adc12_*`、`mathacl_*`、`iqmath_*`：各外设照抄改。

### 立创天猛星 wiki（中文，最适合电赛队友）
- **简易 PID 入门套件**：带编码器电机 + TB6612，PID 实现定速/定距，屏幕显示 PID 参数与目标/当前曲线——电赛 PID 闭环最佳起步样例。
- 编码器驱动 / PWM 输出 / 电机驱动 / 串口 章节，逐个外设有图文 + 代码。

### 社区开源工程（可点名抄）
| 项目 | 平台 | 内容 |
|---|---|---|
| **danshoujieyi/TI-MSPM0G3507** | GitHub | 工程模板：裸机 + FreeRTOS + RT-Thread 三版，Keil5+VSCode 开发 |
| **2024 电赛 H 题循迹小车源码** | CSDN/GitCode | 完整循迹小车（含单圈 ~15s 成绩），可参考整体架构 |
| **电赛 2024 H 题智能小车（8 路灰度 + MPU6050）** | CSDN | 双环 PID + 灰度+IMU 方案的项目报告 |
| **lcsc/easy-pid-beginner-kit** | Gitee | 天猛星 PID 入门套件官方开源工程 |
| **基于 MSPM0G3507 的 PID 入门套件** | 立创开源(oshwhub) | PID 工程 + 硬件 |

## 参考链接

- [LP-MSPM0G3507 LaunchPad（TI 官方）](https://www.ti.com/tool/LP-MSPM0G3507)
- [立创·天猛星 MSPM0G3507 技术文档中心（lckfb wiki）](https://wiki.lckfb.com/zh-hans/tmx-mspm0g3507/)
- [编码器驱动（天猛星 PID 入门套件 wiki）](https://wiki.lckfb.com/zh-hans/tmx-mspm0g3507/training/easy-pid-beginner-kit/encoder-drives.html)
- [PWM 输出（天猛星 wiki）](https://wiki.lckfb.com/zh-hans/tmx-mspm0g3507/ccs-beginner/pwm.html)
- [LCKFB-TMX-MSPM0G3507 开发板（立创商城，5 片 ≈29.9 元）](https://item.szlcsc.com/44281600.html)
- [danshoujieyi/TI-MSPM0G3507 工程模板（GitHub）](https://github.com/danshoujieyi/TI-MSPM0G3507)
- [easy-pid-beginner-kit（Gitee 立创官方）](https://gitee.com/lcsc/easy-pid-beginner-kit)
- [基于 MSPM0G3507 的 PID 入门套件（立创开源）](https://oshwhub.com/monch/mspm0g3507-based-pid-starter-kit)
- [24 电赛 H 题循迹小车 MSPM0G3507 源码（CSDN）](https://blog.csdn.net/gitblog_09818/article/details/141974514)
- [电赛 2024 H 题智能小车 8 路灰度+MPU6050 项目报告（CSDN）](https://blog.csdn.net/weixin_60991529/article/details/141832409)
- [WeAct MSPM0G3507 开发板（CNX Software）](https://www.cnx-software.com/2025/02/14/weact-mspm0g3507-development-board-texas-instruments-mspm0g3507srhbr-cortex-m0-mixed-signal-mcu/)
