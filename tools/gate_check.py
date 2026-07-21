#!/usr/bin/env python3
"""任务级门校验 CLI（确定性，无 LLM）——校验某任务声明的确定性门已 PASS、人工签字已 approved。

board.py done 内部用同一逻辑（gatelib.check_spec）；本 CLI 供单人编排子代理在
标完成前独立自检，两边共用一份判据，杜绝漂移。

用法:
    python tools/gate_check.py <task-id>
PASS -> exit 0；未过 -> exit 1。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board    # noqa: E402  —— 单一 DAG 来源（含每任务 gate/signoff 声明）
import gatelib  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    tid = sys.argv[1]
    spec = board.TASKS.get(tid)
    if spec is None:
        print(f"未知任务: {tid}"); sys.exit(2)
    gate, signoff = spec.get('gate'), spec.get('signoff')
    if not gate and not signoff:
        print(f"✓ [{tid}] 无门/签字要求，可直接完成。"); sys.exit(0)
    ok, problems = gatelib.check_spec(spec)
    head = f"任务 [{tid}]  门={gate or '—'}  签字={signoff or '—'}"
    if ok:
        print(f"✓ {head} —— 全部通过。"); sys.exit(0)
    print(f"✗ {head} —— 未满足：")
    for p in problems:
        print(f"   - {p}")
    sys.exit(1)


if __name__ == '__main__':
    main()
