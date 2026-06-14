# 接线表 (harness) —— MSPM0G3507

> 由 tools/render_wiring.py 从 contracts/pinmap.yaml 生成。照此连线；连完逐行打勾。

| ✓ | MCU 引脚 | 功能 | 外设 | 模块 | 对端引脚 | 备注 |
|---|---|---|---|---|---|---|
| ☐ | PA0 | PWM | TIMA0 | TB6612#1 | PWMA |  |
| ☐ | PA4 | GPIO |  | TB6612#1 | AIN1 |  |
| ☐ | PA5 | GPIO |  | TB6612#1 | AIN2 |  |
| ☐ | PA1 | PWM | TIMA0 | TB6612#1 | PWMB |  |
| ☐ | PA6 | GPIO |  | TB6612#1 | BIN1 |  |
| ☐ | PA7 | GPIO |  | TB6612#1 | BIN2 |  |
| ☐ | PB13 | GPIO |  | TB6612#1 | STBY |  |
| ☐ | PA2 | PWM | TIMA1 | servo | SIG | 50Hz, 独立5-6V供电 |
| ☐ | PA8 | QEI_A | TIMG0 | encoderL | A |  |
| ☐ | PA9 | QEI_B | TIMG0 | encoderL | B |  |
| ☐ | PA10 | QEI_A | TIMG1 | encoderR | A |  |
| ☐ | PA11 | QEI_B | TIMG1 | encoderR | B |  |
| ☐ | PA12 | UART_TX | UART1 | K230 | RXD |  |
| ☐ | PA13 | UART_RX | UART1 | K230 | TXD |  |
| ☐ | PA14 | UART_TX | UART0 | USB-TTL | RXD | VOFA+ JustFloat |
| ☐ | PB0 | I2C_SDA | I2C0 | OLED+IMU | SDA |  |
| ☐ | PB1 | I2C_SCL | I2C0 | OLED+IMU | SCL |  |
| ☐ | PB2 | ADC | ADC0 | 8ch-grayscale | CH0 |  |
| ☐ | PB3 | ADC | ADC0 | 8ch-grayscale | CH1 |  |
| ☐ | PB4 | ADC | ADC0 | 8ch-grayscale | CH2 |  |
| ☐ | PB5 | ADC | ADC0 | 8ch-grayscale | CH3 |  |
| ☐ | PB6 | ADC | ADC0 | 8ch-grayscale | CH4 |  |
| ☐ | PB7 | ADC | ADC0 | 8ch-grayscale | CH5 |  |
| ☐ | PB8 | ADC | ADC0 | 8ch-grayscale | CH6 |  |
| ☐ | PB9 | ADC | ADC0 | 8ch-grayscale | CH7 |  |
| ☐ | PB10 | ADC | ADC0 | divider |  | 低电量监测 |
| ☐ | PB14 | GPIO |  | button | START |  |
| ☐ | PB15 | GPIO |  | button | MODE |  |
| ☐ | PA17 | GPIO |  | buzzer | SIG |  |
| ☐ | PA20 | SWD_IO |  | debugger | SWDIO |  |
| ☐ | PA21 | SWD_CLK |  | debugger | SWCLK |  |

## 接线铁律
- K230↔MCU 串口 **TX↔RX 交叉，必须共地**（见 contracts/protocol）。
- 舵机/电机用**独立电源轨**，勿挂 3.3V 逻辑轨（见 design/power）。
- 上电先量各轨电压，再插模块。