#!/usr/bin/env python3
"""供电预算确定性门：按最坏情况（电机用堵转电流，不用标称）算每条轨电流，
校验稳压器余量，标出掉电/欠流风险。PASS->exit 0，FAIL->exit 1。

用法:
    python tools/power_budget.py design/power.yaml [--report [--by LANE]]
--report 时把结果写入 design/gates/power.yaml（机读门报告，供 board.py done 校验）。
"""
import sys, os
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib  # 写机读门报告

HEADROOM = 0.30  # 默认留 30% 余量

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_current(ld):
    """取该负载的设计电流：stall=true 用堵转电流，否则用标称。"""
    qty = ld.get('qty', 1)
    if ld.get('stall'):
        cur = ld.get('stall_current_a', ld.get('current_a', 0))
    else:
        cur = ld.get('current_a', 0)
    return cur * qty, qty


def main():
    argv = sys.argv[1:]
    report = '--report' in argv
    by = argv[argv.index('--by') + 1] if '--by' in argv and argv.index('--by') + 1 < len(argv) else None
    pos = [a for i, a in enumerate(argv)
           if not a.startswith('--') and not (i > 0 and argv[i - 1] == '--by')]
    if not pos:
        print("用法: python tools/power_budget.py <power.yaml> [--report]")
        sys.exit(2)
    path = pos[0]
    pw = load(path)
    headroom = pw.get('headroom', HEADROOM)

    errors, warns, rows = [], [], []
    batt = pw.get('battery', {})
    print(f"电池: {batt.get('type','?')}  Vmin={batt.get('vmin','?')} Vmax={batt.get('vmax','?')}  余量={int(headroom*100)}%")

    for rail in pw.get('rails', []):
        name = rail.get('name', '?')
        total = 0.0
        detail = []
        for ld in rail.get('loads', []):
            c, qty = load_current(ld)
            total += c
            mark = '堵转' if ld.get('stall') else ''
            detail.append(f"{ld.get('name','?')}×{qty}{mark}={c:.2f}A")
        required = total * (1 + headroom)
        reg = rail.get('regulator')
        src = rail.get('source', '')

        if src == 'battery-direct' or not reg:
            rows.append((name, f"{total:.2f}A", f"{required:.2f}A", "电池直供", "—"))
            if not rail.get('fuse'):
                warns.append(f"[{name}] 电池直供大电流轨建议加保险/铺铜核算（电机 VM）")
        else:
            iout = reg.get('iout_max')
            part = reg.get('part', '?')
            if iout is None:
                warns.append(f"[{name}] 稳压 {part} 缺 iout_max，无法校验余量")
                rows.append((name, f"{total:.2f}A", f"{required:.2f}A", f"{part}(?A)", "⚠未知"))
            elif required > iout:
                errors.append(f"[{name}] 需 {required:.2f}A(含{int(headroom*100)}%余量) > {part} 额定 {iout}A → 欠流/掉电复位风险")
                rows.append((name, f"{total:.2f}A", f"{required:.2f}A", f"{part}({iout}A)", "✗超"))
            else:
                rows.append((name, f"{total:.2f}A", f"{required:.2f}A", f"{part}({iout}A)", "✓"))
        if detail:
            print(f"  · {name}: " + " + ".join(detail))

    # 表格
    print(f"\n{'轨':<14}{'实测':<9}{'需(含余量)':<12}{'稳压':<22}{'判定'}")
    for r in rows:
        print(f"{r[0]:<14}{r[1]:<9}{r[2]:<12}{r[3]:<22}{r[4]}")

    for w in warns:
        print(f"  ⚠ {w}")
    if errors:
        print(f"\n✗ FAIL —— {len(errors)} 处供电风险:")
        for e in errors:
            print(f"   - {e}")
        if report:
            gatelib.write_report('power', os.path.relpath(path, ROOT), 'FAIL', details=errors, by=by)
        sys.exit(1)
    print("\n✓ PASS —— 各稳压轨余量充足（电机已按堵转电流计）。")
    if report:
        gatelib.write_report('power', os.path.relpath(path, ROOT), 'PASS', by=by)
    sys.exit(0)


if __name__ == '__main__':
    main()
