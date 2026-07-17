# SysConfig 引脚配置清单（由 contracts/pinmap.yaml 导出）

> 在 CCS 的 SysConfig 里照此配外设与引脚，生成 `ti_msp_dl_config.c`。完整接线对端见 `design/harness.md`。
> ⚠ 引脚能力表 verified:false——配之前用 SysConfig 自身的引脚冲突提示再核一遍。

| 外设实例 | 功能 | 引脚 | 用途 |
|---|---|---|---|
| TIMA0 | PWM CH | PA0, PA1 | 左/右轮调速 |
| TIMA1 | PWM CH | PA2 | 舵机(50Hz) |
| GPIO out | — | PA4,PA5,PA6,PA7 | 电机方向 AIN1/2 BIN1/2 |
| GPIO out | — | PB13 | TB6612 STBY |
| TIMG0 | QEI A/B | PA8, PA9 | 左轮编码器 |
| TIMG1 | QEI A/B | PA10, PA11 | 右轮编码器 |
| UART1 | TX/RX | PA12, PA13 | K230（交叉、共地，115200 8N1）|
| UART0 | TX | PA14 | VOFA+/日志 |
| I2C0 | SDA/SCL | PB0, PB1 | OLED + MPU6050（共总线）|
| ADC0 | CH×8 | PB2~PB9 | 8 路灰度 |
| ADC0 | CH | PB10 | 电池分压监测 |
| GPIO in | — | PB14, PB15 | 按键 START/MODE |
| GPIO out | — | PA17 | 蜂鸣 |
| SWD | IO/CLK | PA20, PA21 | 调试（勿占用）|

中断优先级（M0+ 仅 4 级，KB08）：控制环/编码器=0 · 串口RX=1 · 调度tick=2 · VOFA/低速=3。
