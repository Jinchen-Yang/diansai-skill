#!/usr/bin/env python3
"""引脚映射确定性门：校验 pinmap.yaml 自洽且符合 MCU 能力表。
PASS -> exit 0；FAIL -> exit 1（CI/提交前必须通过）。

用法:
    python tools/pinmux_check.py contracts/pinmap.yaml [contracts/mcu/<MCU>.yaml]
"""
import sys, os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# function -> (能力表 limits 键, 计数方式)  count=按assignment计, periph=按distinct peripheral计
FAMILY = {
    'PWM':      ('PWM_CHANNEL', 'count'),
    'ADC':      ('ADC_CHANNEL', 'count'),
    'UART_TX':  ('UART', 'periph'), 'UART_RX': ('UART', 'periph'),
    'I2C_SDA':  ('I2C', 'periph'),  'I2C_SCL': ('I2C', 'periph'),
    'SPI_SCLK': ('SPI', 'periph'),  'SPI_MOSI': ('SPI', 'periph'),
    'SPI_MISO': ('SPI', 'periph'),  'SPI_CS':  ('SPI', 'periph'),
    'QEI_A':    ('QEI', 'periph'),  'QEI_B':   ('QEI', 'periph'),
    'CAN_TX':   ('CAN', 'periph'),  'CAN_RX':  ('CAN', 'periph'),
    # GPIO / SWD_IO / SWD_CLK : 无数量上限
}


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    if len(sys.argv) < 2:
        print("用法: python tools/pinmux_check.py <pinmap.yaml> [mcu.yaml]")
        sys.exit(2)
    pinmap_path = sys.argv[1]
    pm = load(pinmap_path)

    mcu = pm.get('mcu')
    cap_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'contracts', 'mcu', f'{mcu}.yaml')
    if not os.path.exists(cap_path):
        print(f"✗ 找不到 MCU 能力表: {cap_path}")
        sys.exit(2)
    cap = load(cap_path)
    pins = cap.get('pins', {})
    limits = cap.get('limits', {})

    errors, warns = [], []
    if not cap.get('verified', False):
        warns.append(f"MCU 能力表 {os.path.basename(cap_path)} verified:false —— PASS 仅表示逻辑自洽，"
                     f"引脚真伪须用 TI SysConfig / 数据手册核实。")

    pin_owner = {}        # pin -> signal
    signal_seen = set()
    fam_count = {}        # limits键 -> int (count方式)
    fam_periph = {}       # limits键 -> set (periph方式)

    for i, a in enumerate(pm.get('assignments', [])):
        tag = a.get('signal', f'#{i}')
        # 必填字段
        for k in ('signal', 'pin', 'function'):
            if not a.get(k):
                errors.append(f"[{tag}] 缺字段 {k}")
        sig, pin, func = a.get('signal'), a.get('pin'), a.get('function')
        if sig:
            if sig in signal_seen:
                errors.append(f"[{tag}] signal 重名")
            signal_seen.add(sig)
        if not pin or not func:
            continue
        # 引脚存在
        if pin not in pins:
            errors.append(f"[{tag}] 引脚 {pin} 不在 {mcu} 能力表中")
            continue
        # 引脚复用冲突
        if pin in pin_owner:
            errors.append(f"[{tag}] 引脚冲突: {pin} 已被 '{pin_owner[pin]}' 占用")
        else:
            pin_owner[pin] = sig
        # 功能合法
        if func not in pins[pin]:
            errors.append(f"[{tag}] 引脚 {pin} 不支持功能 {func}（支持: {', '.join(pins[pin])}）")
        # 数量门累计
        if func in FAMILY:
            key, mode = FAMILY[func]
            if mode == 'count':
                fam_count[key] = fam_count.get(key, 0) + 1
            else:
                per = a.get('peripheral')
                if not per:
                    warns.append(f"[{tag}] 功能 {func} 建议补 peripheral 字段以便数量门精确统计")
                else:
                    fam_periph.setdefault(key, set()).add(per)

    # 数量门比对
    for key, n in fam_count.items():
        lim = limits.get(key)
        if lim is not None and n > lim:
            errors.append(f"数量超限: {key} 用了 {n}，上限 {lim}")
    for key, s in fam_periph.items():
        lim = limits.get(key)
        if lim is not None and len(s) > lim:
            errors.append(f"数量超限: {key} 实例 {sorted(s)} 共 {len(s)}，上限 {lim}")

    # 报告
    n_assign = len(pm.get('assignments', []))
    print(f"pinmap: {os.path.relpath(pinmap_path, ROOT)}  | MCU: {mcu}  | 分配 {n_assign} 项")
    for w in warns:
        print(f"  ⚠ {w}")
    if errors:
        print(f"✗ FAIL —— {len(errors)} 处问题:")
        for e in errors:
            print(f"   - {e}")
        sys.exit(1)
    used = {**fam_count, **{k: len(v) for k, v in fam_periph.items()}}
    print(f"✓ PASS —— 引脚无冲突、功能合法、数量未超限。占用: "
          + ", ".join(f"{k}={v}/{limits.get(k,'?')}" for k, v in sorted(used.items())))
    sys.exit(0)


if __name__ == '__main__':
    main()
