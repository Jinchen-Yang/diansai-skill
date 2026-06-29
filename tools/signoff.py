#!/usr/bin/env python3
"""人工签字 CLI（确定性，无 LLM）——把"用户批准了某个人工门"落成可提交状态。

skill 到人工门时，先用 AskUserQuestion 取得用户明确选择，再调本工具写状态；
board.py done / gate_check.py 会校验对应签字为 approved 才放行。

用法:
    python tools/signoff.py approve <gate> [--note "..."] [--by lead]
    python tools/signoff.py reject  <gate> [--note "..."] [--by lead]
    python tools/signoff.py pending <gate> [--note "..."]
    python tools/signoff.py status  [<gate>]
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib  # noqa: E402


def _opt(args, key):
    return args[args.index(key) + 1] if key in args else None


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    cmd = args[0]
    if cmd in ('approve', 'reject', 'pending'):
        if len(args) < 2:
            print(f"用法: signoff.py {cmd} <gate> [--note ..] [--by ..]"); sys.exit(2)
        gate = args[1]
        status = {'approve': 'approved', 'reject': 'rejected', 'pending': 'pending'}[cmd]
        rec = gatelib.set_signoff(gate, status, note=_opt(args, '--note'), by=_opt(args, '--by'))
        print(f"✓ 签字 [{gate}] → {rec['status']}"
              + (f"（by {rec['by']}）" if rec.get('by') else '')
              + (f"  备注: {rec['note']}" if rec.get('note') else ''))
    elif cmd == 'status':
        items = gatelib.load_signoffs()
        if len(args) > 1:
            st = gatelib.signoff_status(args[1])
            print(f"{args[1]}: {st or '未签'}")
        elif not items:
            print("（暂无签字记录）")
        else:
            for s in items:
                print(f"  {s['gate']}: {s.get('status','?')}"
                      + (f"  by {s['by']}" if s.get('by') else '')
                      + (f"  — {s['note']}" if s.get('note') else ''))
    else:
        print(__doc__); sys.exit(2)


if __name__ == '__main__':
    main()
