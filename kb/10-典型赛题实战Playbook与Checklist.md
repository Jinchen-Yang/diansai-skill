---
title: "🚀 典型赛题实战 Playbook 与 Checklist"
tags:
  - 电赛/实战
  - checklist
aliases:
  - "小车类赛题实战手册：从拿题到完赛的全流程 Playbook（MSPM0 + K230）"
  - "10 典型赛题实战 Playbook 与 Checklist"
created: 2026-06-13
---

> [!nav] 导航
> [[00-总览MOC|📖 总览]] · ⬅ [[09-开源资源与备赛经验|09 开源资源与备赛经验]]

# 🚀 典型赛题实战 Playbook 与 Checklist

> [!abstract] 本篇速览
> 送药/追踪/循迹打法、技术栈组合、三张赛前赛中赛后清单

## 一、通用 Playbook：从拿到题目到完赛

小车类赛题（送药小车、运动目标追踪、循迹避障、双车跟随、色块/数字识别）虽题面各异，但完赛节奏高度一致。固定按下面 8 步推进，能最大化 4 天 3 夜的产出。

### 1. 需求与指标拆解（拿题后 0.5~1 小时，全队一起做）
- 把题目"基本要求 + 发挥部分"逐条抄成 checklist，每条标注**分值、限时、误差容限、是否可独立验收**。例如 2024 H 题"A→B 停车，≤15s，声光提示"；2021 F 题送药小车"运送+返回均 <20s，超时扣分"。
- 画**场地尺寸图**（H 题场地 ≥220cm×120cm、半圆弧 R=40cm、线宽 1.8cm；F 题走廊黑实线为墙、红实线居中、黑色数字纸标病房号）。
- 提炼**硬约束**：H 题"必须 MSPM0 系列 MCU、禁止摄像头、只能前进、车体 ≤25×15×15cm"；这类约束直接决定方案，先于一切。
- 输出一张《分值-难度矩阵》，按"分值/工时"性价比排序，决定先打哪几问。**基本要求 100% 拿满优先于发挥部分**。

### 2. 方案与器件选型（1~2 小时）
按题型套用第二节的"推荐技术栈组合"。核心决策点：
- **要不要视觉**：题面禁摄像头（如 24H 题）→ 纯灰度阵列；需识别数字/色块/光斑 → 上 K230。
- **底盘形态**：循迹/送药用两轮差速+万向轮（转向灵活、PID 简单）；高速直线题可四驱。
- **定位手段**：编码器里程计（必备）+ 灰度循迹 + 可选 IMU（陀螺仪积分测航向，弯道/原地转必备）。

### 3. 任务分工（三人队）
| 角色 | 职责 | 关键交付 |
|---|---|---|
| 电控/软件（负责人） | MSPM0 底层驱动、PID、状态机、与 K230 联调 | 可跑的运动控制 + 通信协议 |
| 视觉/算法 | K230 CanMV 巡线/识别/坐标回传、阈值标定 | 稳定输出的数据包 |
| 硬件/结构 | 底盘、电源、传感器布线、PCB/洞洞板、论文 | 不松动的车 + 测试数据 |
负责人是"集成中枢"，要定义**通信协议**（见第四节），让视觉同学按协议发包，自己按协议收包，二者并行开发。

### 4. 搭建最小可运行系统 MVP（第 1 天必须完成）
MVP = 车能**前进+差速转向+读到编码器+串口能打印**。顺序：电机正反转 → PWM 调速 → 编码器测速 → 速度环 PID 闭环 → 串口 printf 调试通道。这一步打通，后面全是叠加。

### 5. 分模块开发与联调顺序（强约束，别跳步）
```
底层驱动(GPIO/PWM/Timer) → 编码器速度环PID → 循迹/定位(灰度或视觉) →
转向/位置环 → 任务状态机 → 视觉识别(数字/色块) → 通信集成 → 整车联调 → 鲁棒性
```
**先把单模块在最简条件下验通，再两两联调**。最忌一上来写整车状态机然后整体调，出问题无法定位。

### 6. 参数整定（PID 调参口诀）
速度环用**增量式 PID**（无累积、抗饱和好）；位置/航向环用**位置式 PID**（带积分限幅）。调参：先纯 P 加到临界振荡 → 退 60% → 加 D 抑制超调 → 最后小量 I 消静差。循迹偏差环 P 主导、D 辅助、I 几乎为 0。每次只改一个参数并记录。

### 7. 鲁棒性/异常/边界处理（拉开名次的地方）
- 丢线/丢目标：记忆上一次偏差方向，原地小幅搜索而非乱冲。
- 串口丢包：帧头帧尾+校验和，收不全就丢弃整帧（实测会出现 8 字节收到 7 字节）。
- 路口/分岔：用编码器里程 + 灰度"全黑/全白"特征做事件触发，别只靠单一传感器。
- 停车精度：接近目标点降速（梯形减速），用编码器闭环定位到点。

### 8. 演示与论文（边做边写，留出半天）
测试数据**当场记录进 Excel**（每问跑 5~10 次记成功率/用时）。论文按官方模板：摘要、方案论证与比较、理论分析与计算、电路与程序设计、测试方案与结果、结论。三人一队、本/专科在校生，竞赛结束上交《设计报告》+ 实物 + 登记表封存。

---

## 二、五类典型题的推荐技术栈组合

| 题型 | 主控 | 底盘/电机 | 传感 | 控制算法 | 视觉/通信 |
|---|---|---|---|---|---|
| **智能送药小车**（21F 类） | MSPM0G3507 | 双 TB6612 + MG513 编码电机(减速比 30/28) | 灰度阵列循迹 + 编码器 + IR 检测装载 | 循迹偏差 PID + 位置环 + 状态机 | K230 巡线+数字识别，UART 回传病房号/偏差 |
| **运动目标控制与追踪**（23E 类） | MSPM0/STM32 | 二维云台(2× 舵机或步进) | K230 摄像头 | 红激光开环画框 + 绿激光增量式 PID 闭环追踪 | K230 find_blobs 输出光斑坐标 → UART |
| **循迹避障小车** | MSPM0G3507 | TB6612 + 编码电机 | 8 路灰度 + 超声波/红外测距 | 循迹 PID + 避障状态机 | 可选 K230，纯灰度更稳 |
| **双车通信/跟随** | 2×MSPM0 | 同上 | 编码器 + 测距(超声/视觉) | 领航车里程同步 + 跟随车距离 PID | NRF24L01(SPI, 2.4G) 或 UART 有线 |
| **色块/数字识别+运动** | MSPM0G3507 | TB6612 + 编码电机 | K230 + 编码器 | 识别触发 + 运动 PID | K230 KPU(MNIST/分类) + UART |

**禁摄像头题（如 24H）**：纯 8 路灰度 + 编码器里程 + IMU 航向，方案最稳，无需视觉。

---

## 三、K230（CanMV）核心代码模板

### 3.1 巡线：快速线性回归 get_regression
返回 `Line` 对象，关键属性 `theta()`（直线角度，0~179°）、`rho()`（到原点距离）、`magnitude()`（拟合强度，越大越像直线）。巡线时车在线正上方，理想直线竖直，`theta≈0/180`；偏差由直线位置 + 角度共同给出。

```python
import time
from media.sensor import *; from media.display import *; from media.media import *
from machine import UART, FPIOA

fpioa = FPIOA()
fpioa.set_function(11, FPIOA.UART2_TXD); fpioa.set_function(12, FPIOA.UART2_RXD)
uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS,
            parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)

sensor = Sensor(); sensor.reset()
sensor.set_framesize(width=320, height=240)
sensor.set_pixformat(Sensor.GRAYSCALE)
GRAYSCALE_THRESHOLD = [(0, 60)]   # 黑线阈值，越暗越接近0
sensor.run()
while True:
    img = sensor.snapshot()
    line = img.get_regression(GRAYSCALE_THRESHOLD, robust=True)
    if line and line.magnitude() > 8:
        theta = line.theta()                       # 角度
        # 角度归一到 [-90,90]，并把直线x位置偏差一起算入
        err_angle = theta - 90 if theta > 90 else theta - (-90 if theta < -90 else 0)
        cx = (line.x1() + line.x2()) // 2
        err_pos = cx - 160                          # 图像中心偏差(320宽)
        err = int(0.7*err_pos + 1.5*err_angle)      # 融合偏差
        # 发包: 帧头0xFF + 偏差(有符号,16bit) + 校验 + 帧尾0xFE
        e = err & 0xFFFF
        cs = ((e>>8) ^ (e&0xFF)) & 0xFF
        uart.write(bytes([0xFF, (e>>8)&0xFF, e&0xFF, cs, 0xFE]))
        img.draw_line(line.line(), color=127)
```

### 3.2 色块/光斑追踪：find_blobs（LAB 空间）
用 CanMV IDE → 工具 → 阈值编辑器标定 LAB 阈值 `(Lmin,Lmax,Amin,Amax,Bmin,Bmax)`。blob 关键属性：`cx() cy()`（中心，用于追踪）、`pixels()`、`area()`、`code()`（多颜色编号）。

```python
RED = (30, 100, 40, 90, 10, 70)   # 红光斑/红色块 LAB，需现场标定
blobs = img.find_blobs([RED], pixels_threshold=50, area_threshold=50, merge=True)
if blobs:
    b = max(blobs, key=lambda x: x.pixels())   # 取最大块
    cx, cy = b.cx(), b.cy()
    ex, ey = cx - 160, cy - 120                # 相对图像中心偏差
    uart.write(bytes([0xFF, cx&0xFF, (cx>>8)&0xFF, cy&0xFF, (cy>>8)&0xFF, 0xFE]))
```
云台追踪：把 `ex/ey` 分别送两路 PID，输出舵机/步进角度。23E 题策略——红激光云台**开环**沿屏幕边线画框，绿激光云台对"两激光点距离差"做**增量式 PID**闭环。

### 3.3 数字识别
K230 用 KPU 跑 MNIST/自训练分类模型识别病房号（28×28 灰度）；识别置信度最高的类别经 UART 回传一个字节即可。送药小车实测：神经网络识别率 ~94%，优于模板匹配。注意 K230 有 5 个 UART，UART0/UART3 被系统占用，用户用 **UART1/UART2/UART4**。

---

## 四、MSPM0G3507 电控核心（负责人主战场）

### 4.1 外设与引脚要点
- **PWM**：TIMA/TIMG 做电机 PWM，常用 ~20kHz（避开可闻噪声）。占空比满量程示例取 ±3200。
- **编码器**：用 TIMER 的 QEI 模式或输入捕获双边沿计数读 AB 相，定时（如 10ms）读计数算转速。
- **电机驱动**：TB6612（双路，AIN1/AIN2/BIN1/BIN2 定方向 + PWMA/PWMB 调速 + STBY 使能），小电流也可 DRV8833。
- **UART**：4 个用户串口，独立 TX/RX 4 级 FIFO，支持中断+DMA。波特率与 K230 对齐 115200。
- 开发用 **CCS Theia + SysConfig 图形化配引脚 + DriverLib**；外设中断名在生成的 `ti_msp_dl_config.h` 里查。

### 4.2 增量式速度环 PID（推荐 C 结构）
```c
typedef struct { float Kp, Ki, Kd, err, err1, err2, out; } PID_t;
float PID_Inc(PID_t *p, float target, float feedback){
    p->err = target - feedback;
    p->out += p->Kp*(p->err - p->err1)
            + p->Ki*p->err
            + p->Kd*(p->err - 2*p->err1 + p->err2);
    p->err2 = p->err1; p->err1 = p->err;
    if(p->out >  3200) p->out =  3200;     // 输出限幅
    if(p->out < -3200) p->out = -3200;
    return p->out;
}
```
位置式 PID 用于航向/定点，需**积分限幅**（如 ±400）防积分饱和。差速转向：`leftPWM = base - turn; rightPWM = base + turn;`，turn 来自循迹偏差环输出。

### 4.3 UART 收 K230 数据包（状态机 + 校验，抗丢包）
```c
volatile int16_t g_err; volatile uint8_t g_flag;
void UART_IRQHandler(void){
    static uint8_t st=0, h=0, l=0, cs=0;
    uint8_t b = DL_UART_Main_receiveData(UART_INST);   // 取一字节
    switch(st){
        case 0: if(b==0xFF) st=1; break;               // 等帧头
        case 1: h=b; st=2; break;
        case 2: l=b; st=3; break;
        case 3: cs=b; st=4; break;
        case 4:
            if(b==0xFE && cs==(uint8_t)((h^l))){        // 校验+帧尾
                g_err=(int16_t)((h<<8)|l); g_flag=1;
            }
            st=0; break;
    }
}
```
**联调踩坑**：收到 7/8 字节是常态——必须丢弃整帧重同步；切勿用阻塞 `receiveDataBlocking` 在主循环收包，会卡死控制周期。

---

## 五、双车通信/跟随

- **无线**：NRF24L01（2.4G，SPI 接 MCU，空旷 100~200m，室内穿墙 10 多米），自定义协议帧、低延迟，比蓝牙更易精确同步；可点对点或 1 收 6 发。
- **有线/红外**：红外对管交换信息，需精确对准、易受光干扰，仅作备用。
- **同步策略**：领航车广播自身里程/状态，跟随车对"目标距离-实测距离"做 PID 保持车距；启动同步用一个握手字节。21F 题双车协同曾用 ZigBee 共享位置。

---

## 六、三张清单

### 6.1 赛前器件 & 工具 Checklist
- 主控：MSPM0G3507 核心板 ×2~3、STM32 备用板、CanMV K230 ×1（备 SD 卡/镜像）
- 驱动/电机：TB6612 模块 ×4、MG513 编码电机 ×4、备用电机
- 传感：8 路灰度模块、超声波 HC-SR04、MPU6050/6500 IMU、红外对管、NRF24L01 ×2
- 电源：3S 锂电/18650 + DC-DC（5V/3.3V）、稳压模块、独立给舵机/电机供电
- 结构：亚克力/铝合金底盘、万向轮、轮子、铜柱、扎带、3M 双面胶、热熔胶
- 工具：仿真器(XDS110/ST-Link)、万用表、示波器、逻辑分析仪、电烙铁、杜邦线/排针、热缩管、USB-TTL
- 软件环境：CCS Theia + MSPM0 SDK + SysConfig、CanMV IDE、串口助手、Keil（备用）
- 耗材：黑色电工胶带、A4 白纸、备用保险/MOS、面包板/洞洞板

### 6.2 赛中开发 & 调试 Checklist
- [ ] 电机能正反转、PWM 调速线性
- [ ] 编码器双轮计数方向正确、测速无跳变
- [ ] 速度环闭环、左右轮速度一致
- [ ] 灰度阈值现场标定（场地光照下重标）
- [ ] 循迹偏差环 P/D 整定、直道不画龙
- [ ] 弯道/路口事件检测可靠（里程+灰度双确认）
- [ ] K230 阈值现场标定、输出坐标稳定
- [ ] UART 双向通；丢包重同步验证
- [ ] 状态机全流程跑通、声光提示正确
- [ ] 停车精度/限时达标，跑 ≥5 次记成功率
- [ ] 低电量时复测（电压降会改变 PID 表现）

### 6.3 提交物 Checklist
- [ ] 设计报告/论文（摘要+方案论证+理论计算+电路程序+测试结果+结论）
- [ ] 测试数据表（每问成功率、用时、误差）
- [ ] 实物（贴编号、确保可复现演示）
- [ ] 登记表 / 作品清单
- [ ] 源代码与原理图归档备份

---

## 七、"软硬件联调 + K230 联调"踩坑与排查顺序

**联调黄金顺序：先各自自测，再合并。** 排查按下面层层下探：

1. **电气层**：共地了吗？K230 TX→MCU RX、MCU TX→K230 RX 交叉接对了吗？电平都是 3.3V 吗？（最高频错误：忘记共地、TX/RX 接反）
2. **物理串口层**：两端波特率/数据位/停止位/校验完全一致（115200,8N1）。先让 K230 单发固定字节，MCU 用串口助手/printf 验证收到原始字节。
3. **协议层**：帧头帧尾+校验和对齐；用逻辑分析仪抓波形确认帧完整。出现少字节→状态机丢帧重同步。
4. **时序层**：K230 出帧速率 vs MCU 控制周期匹配；MCU 收包用中断+缓冲，**禁止阻塞**拖垮控制环。
5. **语义层**：坐标系一致（图像中心 vs 车体中心）、符号方向一致（偏左为正还是为负），用打印偏差值人工挪车验证。
6. **闭环层**：偏差→PID→电机方向正确（接反会正反馈发散）；先低速验证再提速。

**硬件联调通用：** 电机不转先量驱动使能(STBY)和供电；编码器乱跳查 AB 相接线和上拉；PID 发散先确认反馈符号；行为随电量变化先稳压再调参。


---

## 🔑 关键要点（速记）

- 拿题先做指标拆解+分值矩阵：基本要求100%拿满优先于发挥部分；先抄全限时/误差/硬约束（如24H题禁摄像头、必须MSPM0、只能前进、车体≤25×15×15cm）。
- 联调顺序是铁律：底层驱动→编码器速度环PID→循迹/定位→位置/航向环→状态机→视觉识别→通信集成→整车→鲁棒性；先单模块自测再两两联调，绝不一步到位。
- 负责人核心是定义通信协议让视觉/电控并行：帧头0xFF+数据+校验和+帧尾0xFE，115200/8N1；K230用UART1/2/4（UART0/3被系统占用），TX/RX交叉且必须共地。
- K230巡线用get_regression取theta(角度)+直线x位置融合偏差，magnitude过滤伪线；色块/光斑用find_blobs(LAB阈值现场标定)取cx/cy送PID；数字用KPU跑MNIST识别率约94%。
- MSPM0G3507电控：TB6612驱动(STBY/AIN/BIN/PWMx)+QEI读编码器；速度环用增量式PID(抗饱和)，航向/定点用位置式PID并加积分限幅(如±400)，输出限幅±3200。
- K230联调排查按层下探：电气(共地/交叉/3.3V)→串口参数→协议校验→时序匹配→坐标符号一致→闭环反馈符号；收到7/8字节是常态，必须丢整帧重同步，禁用阻塞收包拖垮控制环。
- 双车跟随首选NRF24L01(2.4G/SPI/低延迟，室内穿墙10余米)，领航车广播里程、跟随车对距离做PID保持车距，启动用握手字节同步。
- PID调参口诀：纯P加到临界振荡退60%→加D抑超调→末了小I消静差，每次只改一个参数并记录；接近目标点梯形减速+编码器闭环定点提升停车精度。
- 鲁棒性拉名次：丢线记忆上次方向小幅搜索而非乱冲；路口用里程+灰度双确认触发；低电量必复测因电压降会改变PID表现。
- 提交物边做边备：每问跑≥5次记成功率/用时进Excel；论文按官方模板(摘要/方案论证/理论计算/电路程序/测试结果/结论)，结束上交设计报告+实物+登记表封存。


---

## 🔗 相关笔记

- [[02-历年小车与控制类赛题|02 历年小车与控制类赛题]] — 2011→2024 逐题解析：送药小车、目标追踪、倒立摆、循迹车，命题规律与趋势
- [[07-K230视觉与主控通信|07 K230 视觉与主控通信]] — CanMV K230 视觉任务 + UART 帧协议 + 双端代码（Python/C）
- [[06-PID及衍生控制算法|06 PID 及衍生控制算法]] — 位置式/增量式/串级/模糊PID、前馈、LQR、滤波、整定方法 + C代码
- [[09-开源资源与备赛经验|09 开源资源与备赛经验]] — GitHub 开源仓库、B站教程、复盘帖、团队分工与72h节奏


---

## 📚 参考资料 / 链接

- [2021电赛F题-智能送药小车-国一（含分值/任务流程/经验）](https://blog.csdn.net/my_id_kt/article/details/122589767) — 送药小车国一作品，任务流程、循迹与数字识别经验
- [基于MSPM0G3507的智能送药小车（21F，OPENMV循迹+K210数字+并行PID）](https://blog.csdn.net/weixin_60991529/article/details/140585607) — 主控MSPM0G3507的送药小车完整方案，PID并行调试
- [2021全国电赛真题F——智能送药小车（题目要求/场地）](https://www.eetree.cn/project/687) — 官方题面：黑实线墙、红实线、病房号、限时20s
- [分享21年电赛F题做题记录与经验](https://blog.csdn.net/cyaya6/article/details/132141593) — 实战踩坑与调试经验
- [2024年全国大学生电子设计竞赛H题 自动行驶小车（题面）](https://blog.csdn.net/qq_74395263/article/details/140770258) — 场地220x120、R40弧线、禁摄像头、必须MSPM0
- [2024电赛H题参考方案+核心控制代码——自动行驶小车](https://blog.csdn.net/qq_67319052/article/details/140763678) — H题四问思路与控制代码
- [24年电赛H题 MSPM0G3507 编码电机驱动与通用PID](https://blog.csdn.net/m0_74800695/article/details/140897932) — PWM/方向/增量式与位置式PID、限幅参数
- [2024年电赛H题赛题解析+MSPM0小车学习方案（知乎）](https://zhuanlan.zhihu.com/p/11628498037) — 赛区一等奖方案、参数调试讲解
- [2023电赛思路 E题：运动目标控制与自动追踪系统](https://blog.csdn.net/KDxhd54DWW/article/details/132072468) — 红/绿激光二维云台、OpenMV识别、PID策略
- [2023年电赛E题报告模板（可直接使用，知乎）](https://zhuanlan.zhihu.com/p/647904592) — E题论文/报告结构模板
- [2023年-E题-运动目标控制与自动追踪（立创开源）](https://oshwhub.com/wa-lang/zhuan-tong-zi-kong) — 开源硬件与云台方案
- [K230 CanMV UART 与STM32串口通信 发送接收数据包 附源码](https://blog.csdn.net/weixin_64593595/article/details/144249080) — UART2引脚GPIO11/12、115200、帧头0xFF帧尾0xFE、状态机收包
- [K230 CanMV 色块追踪 颜色识别 blobs 全面详解](https://blog.csdn.net/weixin_64593595/article/details/144187093) — find_blobs参数、LAB阈值编辑器、cx/cy/code属性、多颜色追踪
- [CanMV K230 快速线性回归（巡线）](https://blog.csdn.net/weixin_45020839/article/details/141959258) — get_regression巡线、theta/rho、PID融合偏差
- [K230 CanMV linear_regression_fast 官方例程（特征检测）](https://www.kendryte.com/k230_canmv/zh/main/example/omv/feature_decection.html) — 官方get_regression参数与返回对象说明
- [CanMV K230 MNIST手写数字识别（KPU）](https://blog.csdn.net/stoat04/article/details/135171979) — 28x28灰度、KPU模型推理识别数字
- [MSPM0G3507 UART串口收发、printf重定向、循环缓冲解析自定义协议](https://blog.csdn.net/wo4fisher/article/details/148623504) — SysConfig配置、接收中断、ring buffer、丢帧踩坑
- [CCS配置MSPM0G3507（七）编码器 TIMER-QEI](https://blog.csdn.net/kaneki_lh/article/details/140231496) — QEI编码器配置读AB相
- [CCS配置MSPM0G3507（六）DMA串口发送](https://blog.csdn.net/kaneki_lh/article/details/140207472) — DMA+UART配置步骤
- [TB6612电机驱动模块（立创开发板天猛星MSPM0文档）](https://wiki.lckfb.com/zh-hans/tmx-mspm0g3507/module/control/tb6612-motor-drive-module.html) — STBY/AIN/BIN/PWM引脚定义
- [嘉立创天猛星MSPM0G3507 简易PID项目示例代码](https://blog.csdn.net/WuXiaoMuDeBug/article/details/148357459) — MSPM0G3507 PID示例工程
- [全国大学生电赛历年小车控制类赛题综述及预测](https://blog.csdn.net/h050210/article/details/146017486) — 历年控制类题型规律与趋势预测
- [NRF24L01实现双工功能（最简单方式）](https://blog.csdn.net/weixin_43287964/article/details/120799738) — 双车2.4G无线通信SPI接法与协议
- [2025年全国大学生电子设计竞赛实施过程说明（西交）](http://nuedc.xjtu.edu.cn/static/uploadfile/2025/0715/20250715110803900.pdf) — 官方流程、三人一队、提交与封存要求
- [2025年全国大学生电子设计竞赛试题（nuedc.org 题库）](https://nuedc.org/problems/2025_H%E9%A2%98_%E9%87%8E%E7%94%9F%E5%8A%A8%E7%89%A9%E5%B7%A1%E6%9F%A5%E7%B3%BB%E7%BB%9F.pdf) — 近年真题PDF，含参赛注意事项与评分
- [CanMV K230 开发板介绍（双核RISC-V/KPU/40pin）](https://blog.csdn.net/m0_71934846/article/details/146472403) — K230硬件能力、5个UART、UART0/3被占用


> [!nav] [[00-总览MOC|📖 总览]] · ⬅ [[09-开源资源与备赛经验|09 开源资源与备赛经验]]