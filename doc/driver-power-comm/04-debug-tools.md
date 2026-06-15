# 调试工具（现成好用的）

> 资料采集 · 执行/电源/通信线。对象：电赛现场调 PID、看波形、抓时序、烧/调试固件的工具链。
> 配套：仓库 `kb/08-软件架构与调试工程化.md`（VOFA/匿名/OLED 菜单更全）。

## 1. VOFA+（串口波形上位机，PID 整定神器）★

免费上位机，串口/网口接收数据实时画多通道波形，是电赛调 PID 的事实标配。支持 3 种数据协议：

| 协议 | 格式 | 优点 | 缺点 | 用途 |
|---|---|---|---|---|
| **JustFloat** | 小端 float 数组 + 4 字节固定帧尾 | 高效、多通道高频 | 需 16 进制接收 | **整定 PID**(target/actual/pwm 同屏) |
| **FireWater** | ASCII 文本 `ch1,ch2,...\n` | 可读、像 printf | 字符串解析占带宽 | 通道少、低频、可读调试 |
| **RawData** | 不解析原始字节 | 通用 | 不画波形 | 当普通串口助手 |

### JustFloat 帧格式（官方权威）

```
struct Frame {
    float    ch_data[N];                       // N 个通道, 小端 float, 各 4 字节
    uint8_t  tail[4] = {0x00, 0x00, 0x80, 0x7F};  // 固定帧尾(浮点 +∞ 的字节)
};
```
- 通道值小端排列，末尾追加固定 4 字节帧尾 `00 00 80 7F`，VOFA+ 据此切帧。
- VOFA+ 字节接收区**要勾"十六进制"**，否则乱码。
- 51 单片机 float 是大端，需字节交换；STM32/MSPM0(Cortex-M)本身小端，直接发即可。

### 单片机侧发送 JustFloat（要点代码）

```c
// 直接把 float 数组按内存(小端)发出, 再补帧尾即可
void vofa_justfloat_send(float *ch, uint8_t n){
    static const uint8_t tail[4] = {0x00, 0x00, 0x80, 0x7F};
    uart_send_bytes((uint8_t*)ch, n * 4);   // n 个小端 float 原样发
    uart_send_bytes(tail, 4);               // 帧尾
}
// 用法(放 task_vofa_send, ~50Hz): 
// float d[3] = {target_rpm, actual_rpm, pwm_duty};
// vofa_justfloat_send(d, 3);
```

要点：
- 发送任务放**最低优先级慢任务**(20~50Hz)，别和控制环抢时。
- 调速度环就发 `{目标, 实际, 输出}`，肉眼看超调/稳态误差/振荡，对照 06-PID 整定。
- **在线改参**：VOFA+ 命令面板可回写(如 `p=1.2\n`)，下位机解析后改 PID，免重新烧录。

## 2. 串口助手 / 逻辑分析仪 / 示波器

- **串口助手**(SSCOM、MobaXterm、VOFA RawData)：看原始数据、发指令、握手调试。
- **逻辑分析仪**(廉价 24M 8 通道 + Saleae/PulseView)：抓 I2C/SPI/UART **时序与电平**——通信不通时第一工具，能解码协议帧，定位"是没发出来还是没收到"。
- **示波器**：看 PWM 占空比/频率、电源纹波、电机换向尖峰、信号毛刺(数字问题查硬件根因)。

## 3. SWD 调试 / 烧录

- **SWD**(2 线 SWDIO/SWCLK + GND，可选 RESET)：STM32 用 **ST-Link**，MSPM0 用 **XDS110/板载**，支持下载 + **在线断点/单步/看变量**(实时观察寄存器/内存)。
- CCS(MSPM0)/Keil/STM32CubeIDE 均集成调试器；调试态可改变量、看调用栈。
- 比裸串口 printf 强：能暂停看现场。但**实时控制环不要长时间断点**(电机会失控乱冲，先 motor_stop)。

## 4. 现场调试速记

- PID：VOFA JustFloat 三通道(目标/实际/输出) + 命令面板在线改参，先 P 后 I 再 D。
- 通信不通：逻辑分析仪抓 TX/RX，确认波特率、TX↔RX 交叉、共地、电平。
- 电机怪：示波器看 PWM 波形 + 电源纹波；先开环验证接线再上闭环。
- 无电脑：OLED 菜单 + 三键/旋钮改参写 Flash(见 kb/08)。

## 参考链接

- [VOFA+ JustFloat 官方文档(帧尾 00 00 80 7F)](https://www.vofa.plus/docs/learning/dataengines/justfloat/)
- [VOFA+ 官方文档首页(三协议总览)](https://www.vofa.plus/docs/learning/)
- [VOFA-Protocol-Driver 三协议下位机 C 源码 - GitHub](https://github.com/jelin-sh/VOFA-Protocol-Driver)
- [VOFA+ 三种协议 C 参考代码 - CSDN](https://blog.csdn.net/qq_58114029/article/details/130500327)
- [如何使用 VOFA+ 以 PID 调参为例 - CSDN](https://blog.csdn.net/cyaya6/article/details/129740111)
- [STM32 VOFA+ 上位机 PID 调参 - CSDN](https://blog.csdn.net/AbaAbaxxx_/article/details/142136202)
- [匿名上位机 V7 协议(0xAA 帧头/功能码/SC+AC 校验) - CSDN](https://blog.csdn.net/csol1607408930/article/details/123929485)
