# K230 ↔ 主控 UART 通信（电赛重点 / 高频踩坑点）

> 视觉端（K230/OpenMV）把"色块坐标 / 巡线偏差 / 目标类别"通过 UART 发给主控（MSPM0/STM32），主控做电机/舵机 PID。
> **本队的串口帧协议以 `contracts/protocol.yaml` 为准**（lead 维护，改后跑 `tools/gen_protocol.py` 重生成 `.h/.py`）。本篇是平台层面的事实与方法参考。

## 一、K230 有几个硬件 UART？谁占了？（务必记牢）

K230 共 **5 个 UART 硬件模块（UART0~UART4）**，但**不是都能用**：

| UART | 状态 | 说明 |
|---|---|---|
| **UART0** | ❌ 被**小核**占用 | 小核 shell / 调试串口 |
| UART1 | ✅ 用户可用 | |
| **UART2** | ✅ 用户可用（**推荐**） | 庐山派引出独立座子，接线最方便 |
| **UART3** | ❌ 被**大核**占用 | 大核 shell（CanMV REPL 相关），勿动 |
| UART4 | ✅ 用户可用 | |

**口诀：UART0 小核占、UART3 大核占，用户只用 UART1 / UART2 / UART4。** 误用 UART0/3 会和系统 shell 抢串口导致异常。

## 二、引脚分配（FPIOA 复用）

K230 引脚是**软件可复用**的：先用 `FPIOA` 把某个 GPIO 设成 UARTx 的 TXD/RXD 功能，再 `machine.UART` 初始化。庐山派常用映射（以官方/立创文档为准，不同板子座子不同）：

| 串口 | TXD | RXD | 板上接口 |
|---|---|---|---|
| **UART2（推荐）** | GPIO11 | GPIO12 | GH1.25 4P 座（1=5V, 2=RXD, 3=TXD, 4=GND） |
| UART1 | GPIO3 / GPIO40 | GPIO4 / GPIO41 | 40Pin 排针 |
| UART4 | GPIO48 / GPIO36 | GPIO49 / GPIO37 | 40Pin 排针 |

> 引脚号是逻辑 GPIO 号，**实际焊盘位置看你板子的丝印/原理图**，务必逐一核对再接。

## 三、接线三铁律

1. **TX ↔ RX 交叉**：K230_TXD → MCU_RXD，K230_RXD ← MCU_TXD。（不是 TX 接 TX！）
2. **必须共地 GND-GND**：两板地不连，电平无参考，必乱码。
3. **电平匹配**：K230 与 MSPM0/STM32 都是 **3.3V TTL**，可直连；**不要接 5V 或 RS232 电平**，会烧。

**波特率**：推荐 **115200**（坐标数据量小、实时性足够）。帧率高/数据多可上 230400 / 460800，但**两端必须一致**并实测误码。

## 四、CanMV 里 machine.UART 用法

```python
from machine import UART, FPIOA

# 1) 先用 FPIOA 把引脚复用成 UART2
fpioa = FPIOA()
fpioa.set_function(11, FPIOA.UART2_TXD)
fpioa.set_function(12, FPIOA.UART2_RXD)

# 2) 初始化 UART2
uart = UART(UART.UART2, baudrate=115200,
            bits=UART.EIGHTBITS,
            parity=UART.PARITY_NONE,
            stop=UART.STOPBITS_ONE)
```

| 方法 | 作用 |
|---|---|
| `uart.write(data)` | 发送 bytes/字符串 |
| `uart.read([n])` | 读全部/n 字节；**非阻塞，无数据返回 None** |
| `uart.readline()` | 读到换行的一行 |
| `uart.readinto(buf)` | 读入 bytearray（省内存） |
| `uart.deinit()` | 释放串口 |

构造常量：通道 `UART.UART1/UART2/UART4`；`bits` 用 `UART.EIGHTBITS`；`parity` 用 `UART.PARITY_NONE/PARITY_EVEN/PARITY_ODD`；`stop` 用 `UART.STOPBITS_ONE/STOPBITS_TWO`。

## 五、帧协议设计（与 MCU 约定固定帧头 + 校验 的二进制协议）

定长简单、变长抗扩展。推荐**变长 + 双帧头 + 校验 + 帧尾**结构（本队实际以 `contracts/protocol.yaml` 为准）：

```
| 0xAA | 0x55 | LEN | FUNC | DATA[LEN] | CHK | 0x0D |
  帧头1  帧头2  长度  功能码    数据         校验   帧尾
```

- **双帧头 0xAA 0x55**：单帧头易和数据字节碰撞误同步，双帧头大幅降低误判。
- **LEN**：DATA 字节数（不含头尾校验）；接收端**必做合法性检查**（>缓冲上限直接重同步），否则越界。
- **FUNC 功能码**：区分数据类型，如 0x01=色块坐标、0x02=巡线偏差、0x03=目标类别、0x04=握手/状态。
- **DATA**：坐标 x,y 用 **int16 小端**、偏差 error 用 int16、类别 id / 置信度用 u8——省带宽、跨平台无歧义。
- **CHK**：入门用**和校验**（LEN+FUNC+DATA 累加取低 8 位），高可靠用 **CRC-8**。
- **帧尾 0x0D**：辅助定界，配合状态机重同步。

**抗丢包 = 状态机重同步**：接收用状态机，任一步（帧头/长度/校验/帧尾）不匹配立即**回到找帧头**，丢半截帧而不卡死。**双向握手**：上电后 MCU 发握手帧（FUNC=0x04），K230 回 ACK，确认链路与波特率一致再进工作。

## 六、K230 端（Python）打包发送

```python
import struct
HEAD = b'\xAA\x55'
TAIL = b'\x0D'

def send_frame(func, payload: bytes):
    body = bytes([len(payload), func]) + payload
    chk = 0
    for b in body:
        chk = (chk + b) & 0xFF        # 和校验
    uart.write(HEAD + body + bytes([chk]) + TAIL)

def send_blob(cx, cy):                 # 0x01 色块坐标
    send_frame(0x01, struct.pack('<hh', cx, cy))     # int16 小端 x,y

def send_line_err(error):              # 0x02 巡线偏差
    send_frame(0x02, struct.pack('<h', error))

def send_target(class_id, conf):       # 0x03 目标类别 + 置信度
    send_frame(0x03, bytes([class_id & 0xFF, conf & 0xFF]))
```

> 本队实战应直接 `import contracts/protocol.py`（与主控 `protocol.h` 同源生成），不要手抄常量，避免两端漂移。

## 七、MCU 端（C）接收要点（MSPM0/STM32 通用）

- **RX 中断里只把字节 push 进环形缓冲（ring buffer）**，绝不在中断里解析——否则丢字节。
- 主循环 `protocol_poll()` 跑解析**状态机**（S_H1→S_H2→S_LEN→S_BODY→S_CHK→S_TAIL），任一步失败回 S_H1。
- 解出完整帧后置 `ready` 标志，主循环按 FUNC 取数据喂 PID。
- MSPM0G3507：UART 带 4 级 TX/RX FIFO、支持 DMA，波特率由 IBRD（整数）+FBRD（小数×64）分频，SysConfig 自动算好；中断用 `DL_UART_Main_getPendingInterrupt` + `DL_UART_MAIN_IIDX_RX` + `DL_UART_Main_receiveData`。STM32 换成 `USART_GetITStatus / USART_ReceiveData`，逻辑通用。

> 完整双端代码（含环形缓冲 + 状态机 C 实现）见仓库 `kb/07-K230视觉与主控通信.md` 第三节。

## 八、联调避坑顺序

1. **先回环再互联**：K230 自发自收（TX 接自己 RX）验证串口正常；MCU 同理；再交叉连。
2. **乱码排查顺序**：波特率不一致 → 没共地 → TX/RX 没交叉 → 电平不对（接了 5V）→ 数据位/停止位不符。
3. **变长帧 LEN 一定做合法性检查**，否则野指针/越界。
4. **发送频率别拉满**：30–50Hz 对小车足够，过高反而挤占 MCU 解析时间。
5. **坐标统一 int16 小端、u8 状态**：两端 struct 格式一字不差。

## 关键要点（速记）

- K230 5 个 UART：**UART0 小核占、UART3 大核占，用户只用 UART1/UART2/UART4**；UART2 庐山派有独立座子最方便。
- 引脚先 `FPIOA.set_function` 复用（UART2 = GPIO11 TXD / GPIO12 RXD），再 `machine.UART(UART.UART2, baudrate=115200, ...)`。
- 接线铁律：**TX↔RX 交叉 + 共地 GND + 都是 3.3V TTL 直连**；115200 起步，两端一致。
- `uart.read()` 非阻塞无数据返 None；`write` 发 bytes。
- 帧协议：双帧头 0xAA55 + LEN + FUNC + DATA + 校验 + 帧尾 0x0D；状态机重同步抗丢包；坐标 int16 小端。
- 本队以 `contracts/protocol.yaml` 为准，两端都 import 同源生成的 `protocol.py`/`protocol.h`。
- MCU 端：RX 中断只入环形缓冲，主循环跑状态机解析。
- 乱码排查顺序：波特率→共地→交叉→电平→数据/停止位。

## 参考链接

- K230 CanMV UART 例程（官方，权威）: https://www.kendryte.com/k230_canmv/zh/main/zh/example/peripheral/uart.html
- K230 CanMV UART 模块 API 手册（官方）: https://developer.canaan-creative.com/k230_canmv/dev/zh/api/machine/K230_CanMV_UART%E6%A8%A1%E5%9D%97API%E6%89%8B%E5%86%8C.html
- K230 CanMV FPIOA 使用教程（官方）: https://www.kendryte.com/k230_canmv/zh/main/zh/example/peripheral/fpioa.html
- 立创·庐山派 K230 串口通讯 UART 文档（引脚/座子/接线）: https://wiki.lckfb.com/zh-hans/lushan-pi-k230/basic/uart.html
- 庐山派 UART 模块 API（立创）: https://wiki.lckfb.com/zh-hans/lushan-pi-k230/api/machine/k230_canmv_uart_module_api.html
- 【K230 CanMV】UART 与 STM32 串口通信 发送接收数据包 附源码（CSDN）: https://blog.csdn.net/weixin_64593595/article/details/144249080
- 庐山派 K230 软件开发第三篇——UART 串口（CSDN）: https://blog.csdn.net/weixin_72451481/article/details/144235787
- 从零玩转 CanMV-K230（6）- UART 例程（CSDN）: https://blog.csdn.net/bin_zhang1/article/details/144609165
- 嘉楠勘智 CanMV-K230 大小核操作（CSDN）: https://blog.csdn.net/youngwah292/article/details/139900025
- 01Studio CanMV-K230 UART 文档: https://wiki.01studio.cc/en/docs/canmv_k230/basic_examples/uart/
- MSPM0G3507 UART 收发 + 循环缓冲解析自定义协议（CSDN）: https://blog.csdn.net/wo4fisher/article/details/148623504
