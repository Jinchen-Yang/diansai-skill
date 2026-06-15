# 通信协议（UART / I2C / SPI / CAN）+ 帧协议设计

> 资料采集 · 执行/电源/通信线。对象：K230↔MCU、MCU↔传感器/外设的总线选择与自定义帧协议。
> 配套：仓库 `contracts/protocol.yaml`(K230↔MCU UART 帧，**只 lead 改**，改后 `python tools/gen_protocol.py`)、`kb/07-K230视觉与主控通信.md`。

## 1. 四总线对比

| 协议 | 线数 | 典型速率 | 拓扑 | 上拉/终端 | 全双工 | 距离 | 适用场景 |
|---|---|---|---|---|---|---|---|
| **UART** | 2(TX/RX) (+GND) | 9600~115200 bps，可 ≤几 Mbps | **点对点** | 无 | 是 | 短(板间几十 cm) | **收 K230 视觉**、上位机调试、模块(蓝牙/GPS)——最稳最简 |
| **I2C** | 2(SDA/SCL) | 100k/400k(标准/快速)，HS 3.4M | **多主多从共总线**(地址寻址) | **必须上拉**(3.3V 用 2.2k，5V 用 4.7k) | 半双工 | 短 | IMU(MPU6050)、OLED、EEPROM、多传感器共总线 |
| **SPI** | 4(SCLK/MOSI/MISO/CS) | 10~60Mbps，可 100M+ | 主从(每从机一根 CS) | 无(片选) | 是 | 短 | 高速：OLED、Flash、高速 ADC/传感器 |
| **CAN** | 2(CANH/CANL 差分) | ≤1Mbps@40m | **多节点总线**(广播+仲裁) | **两端各 120Ω 终端电阻** | 半双工 | 长(差分抗干扰) | 多节点、强干扰(电机环境)、车规；电赛少用但多电机/分布式可上 |

**速记选择**：
- 收 **K230 视觉数据 → UART**（点对点最稳，CanMV/protocol 同源）。
- **IMU / OLED 共线 → I2C**（省脚、地址区分；记得上拉）。
- **高速大数据(Flash/高速屏) → SPI**。
- **多节点 + 电机强干扰 + 长线 → CAN**（差分抗干扰，两端 120Ω 必加，少一个会信号反射出错）。

### 接线注意
- **UART 必须 TX↔RX 交叉**(A.TX→B.RX, A.RX→B.TX)，且**共地**；电平要一致(都 3.3V，K230 与 MCU 都是 3.3V)。
- **I2C** SDA/SCL 都要上拉到 VCC；多从机靠 7 位地址区分，地址冲突要改器件 AD0 脚。
- **SPI** 模式(CPOL/CPHA 0~3)主从必须一致；每个从机独立 CS。
- **CAN** 用双绞线，特性阻抗 120Ω，**总线最远两端各一个 120Ω 终端电阻**；需 CAN 收发器(如 TJA1050)。

## 2. 自定义帧协议设计（重点，K230↔MCU）

裸 UART 是字节流，必须设计**帧协议**才能可靠分包。推荐结构：

```
┌────────┬────────┬────────┬─────────────┬────────┐
│ 帧头   │ 长度   │ 类型   │ payload     │ 校验   │
│ 0xAA55 │ len    │ type   │ data[len]   │ CRC/SUM│
│ 2字节  │ 1字节  │ 1字节  │ len 字节    │ 1~2字节│
└────────┴────────┴────────┴─────────────┴────────┘
```

- **帧头**：固定且不易在数据中出现的魔数(如 `0xAA 0x55`)，用于同步起点。
- **长度**：payload 字节数，用于知道该收多少、防越界。
- **类型**：区分帧含义(巡线偏差/目标坐标/数字识别结果/心跳…)。
- **校验**：
  - **和校验(checksum)**：从长度到 payload 末尾逐字节累加取低 8 位，最简、够用。
  - **CRC8/CRC16**：更强，抗多位错；payload 大或干扰强时用。

### 环形缓冲 + 状态机解析（防丢帧关键）

收发节奏不一致、UART 中断字节到达——用**环形缓冲(ring buffer)** 暂存原始字节，主循环里用**状态机**逐字节解析，不在中断里解包。

```c
// 接收状态机: 在 task_k230_parse(5ms) 里跑, 从 ringbuf 取字节
typedef enum { WAIT_H1, WAIT_H2, GET_LEN, GET_TYPE, GET_DATA, GET_CRC } pstate_e;
static pstate_e st = WAIT_H1;
static uint8_t buf[64], idx, len, type, sum;

void frame_parse(void){
    uint8_t b;
    while(ringbuf_get(&b)){                      // 取完缓冲里所有字节
        switch(st){
        case WAIT_H1: if(b==0xAA) st=WAIT_H2; break;
        case WAIT_H2: st = (b==0x55)? GET_LEN : WAIT_H1; break;     // 不对则重新找头
        case GET_LEN: len=b; sum=b; idx=0; st=GET_TYPE; break;
        case GET_TYPE: type=b; sum+=b; st = len? GET_DATA : GET_CRC; break;
        case GET_DATA: buf[idx++]=b; sum+=b; if(idx>=len) st=GET_CRC; break;
        case GET_CRC:
            if(b == (sum&0xFF)) on_frame(type, buf, len);  // 校验过才采信
            st = WAIT_H1; break;                            // 无论对错都复位找下一帧
        }
    }
}
```

要点：
- **中断只收字节进 ringbuf**(µs 级)，解析在主循环——避免中断被拖长、丢字节。
- 校验失败/帧头错→**复位状态机回到找帧头**，自动跳过坏帧、不卡死。
- 可加**超时**：一帧接收超过阈值未完成→丢弃重置(防半截帧卡住)。
- 用 **DMA + 串口空闲(IDLE)中断**收整帧更省 CPU(STM32/MSPM0 都支持)。

## 参考链接

- [UART vs I2C vs SPI 对比 - Seeed Studio](https://www.seeedstudio.com/blog/2019/09/25/uart-vs-i2c-vs-spi-communication-protocols-and-uses/)
- [I2C vs SPI vs UART 速率/线数/场景 - Total Phase](https://www.totalphase.com/blog/2021/12/i2c-vs-spi-vs-uart-introduction-and-comparison-similarities-differences/)
- [UART vs SPI vs I2C 何时用哪个 - logix4u](https://www.logix4u.net/uart-vs-spi-vs-i2c-when-to-use-each-protocol/)
- [CAN 总线入门(120Ω 终端电阻/差分/速率) - 博客园](https://www.cnblogs.com/FROMRPITO0/p/17875251.html)
- [CAN-bus 终端电阻为何重要 - OFweek](https://ee.ofweek.com/2021-07/ART-11000-2802-30513839.html)
- [CAN 总线架构/信号传输原理 - 亿佰特](https://www.ebyte.com/news/3121.html)
- [串口接收完整一帧数据的 3 种方法 - CSDN](https://blog.csdn.net/meilante5190/article/details/106959764)
- [解析协议数据结构：环形缓冲与 CRC 校验 - CSDN](https://blog.csdn.net/u010261063/article/details/119424169)
- [串口数据包(帧头帧尾+队列+校验解包)实现 - CSDN](https://blog.csdn.net/dsafefvf/article/details/149783867)
