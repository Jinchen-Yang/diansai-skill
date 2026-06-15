# firmware/ —— 控制 lane（MSPM0G3507，4 层架构）

分层（KB08）：**HAL/BSP ← Driver ← Middleware ← App**。纪律：App 禁直调 `DL_*`，必经 Driver；Driver 不含比赛逻辑。换芯片只改 BSP/Driver，Middleware/App 共用。

## 结构
```
app/        app_mission.c   FSM 跑送药流程
middleware/ pid.{c,h} scheduler.{c,h} vofa.{c,h}   ← 与芯片无关，可主机编译/单测
driver/     k230_uart.{c,h} motor.{c,h} ...         ← 调 DriverLib，引脚据 pinmap
bsp/        pinmap.md        SysConfig 引脚配置清单
contracts/  protocol.h       K230 收帧（勿手改）
tests/      host_test.c      主机自测
```

## 编译 / 烧录
1. 按 `env/control.md` 装 CCS Theia + MSPM0 SDK + SysConfig。
2. 据 `bsp/pinmap.md` 在 SysConfig 配引脚/外设，生成 `ti_msp_dl_config.c`。
3. XDS110（LaunchPad 板载）烧录调试。

## 主机自测（无需硬件，验中间件+协议）
```sh
cc -std=c11 -Imiddleware -I../../../contracts \
   tests/host_test.c middleware/pid.c middleware/scheduler.c -o /tmp/ht && /tmp/ht
```

## 注意
- driver/app 层的 `TODO(SysConfig/DriverLib)` 是**有意留的 bring-up 接缝**（在 CCS+MSPM0 SDK 里填），不是 bug；可移植中间件 `pid`/`scheduler` 已主机编译验证。
- **控制参数（PID 增益/阈值）= 占位，必须真车整定**（见 `design/test_plan.md`）。
- K230 收帧只用 `contracts/protocol.h`（改协议改 `protocol.yaml` 重生成）。
- **外设 init 逐项对参考手册核对**：时钟树 / PWM 频率 / ADC 采样 / 中断优先级（M0+ 仅 4 级）。
