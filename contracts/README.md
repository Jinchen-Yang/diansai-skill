# 跨 Lane 契约

软件、视觉和硬件联调前，先读本目录。这里的文件是跨团队共享接口，不能按个人项目习惯各自修改。

## K230 <-> MCU UART 协议

`protocol.yaml` 是唯一真值。它定义帧格式、功能码、字段类型、字节序与校验。

```text
protocol.yaml
  -> python tools/gen_protocol.py
  -> protocol.h     给 MSPM0 / STM32 固件包含
  -> protocol.py    给 K230 视觉程序使用
```

### 修改规则

1. 先改 `protocol.yaml`，不得直接改生成的 `protocol.h` 或 `protocol.py`。
2. 在仓库根运行 `python tools/gen_protocol.py`。
3. 将新协议签名和功能变更通知软件与视觉 lane。
4. 主控项目从本目录复制或包含新的 `protocol.h`；K230 项目同步新的 `protocol.py`。
5. 联调前检查 C/Python 中的 `PROTOCOL_SIG` 完全相同。

### 电气与链路

- 3.3V TTL UART，115200 baud，8N1。
- K230 TX 接 MCU RX；K230 RX 接 MCU TX；必须共地。
- 传输帧：`AA 55 LEN FUNC PAYLOAD CHECKSUM 0D`。
- `LEN = FUNC(1B) + PAYLOAD`，校验为 `LEN + FUNC + PAYLOAD` 的低 8 位。
- 主控接收必须采用逐字节状态机，校验失败后可从下一帧头重新同步，不能阻塞等待整帧。

### 当前功能码

| 功能码 | Python 发送函数 | 载荷 | 用途 |
|---|---|---|---|
| `0x01` | `blob_xy(cx, cy)` | `int16 cx, int16 cy` | 色块或光点中心 |
| `0x02` | `line_error(error)` | `int16 error` | 巡线横向误差 |
| `0x03` | `target_class(class_id, confidence)` | `uint8, uint8` | 分类结果与置信度 |
| `0x04` | `handshake(token)` | `uint8 token` | 上电握手或心跳 |
| `0x05` | `aim_offset(dx, dy, found)` | `int16, int16, uint8` | 瞄准偏差；`found=0` 表示链路在线但当前没有目标 |

所有多字节字段使用小端序。图像坐标默认以左上角为原点，向右 `x` 增大、向下 `y` 增大；任务代码若改坐标含义，必须在对应 `vision/tasks/` 文档明确说明，不能暗改协议字段含义。

## 引脚映射

`pinmap.yaml` 是硬件到固件的共同约定。生成或修改后必须运行：

```text
python tools/pinmux_check.py contracts/pinmap.yaml
```

目前正式比赛板的引脚表尚未冻结，软件不得根据样例 pinmap 写死新板引脚。
