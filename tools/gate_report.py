#!/usr/bin/env python3
"""通用门报告记录器（确定性，无 LLM）。

给那些没有专用确定性脚本、但结果可由外部命令判定的门（如固件 `compile`）记录机读报告。
有专用脚本的门（pinmux/power/protocol）由对应工具自带 --report，不必用本工具。

用法:
    python tools/gate_report.py <gate> <target> PASS|FAIL [--by lane] [--detail "..."]
例:
    cc ... && python tools/gate_report.py compile firmware PASS --by 控制
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib  # noqa: E402


def main():
    args = sys.argv[1:]
    if len(args) < 3 or args[2] not in ('PASS', 'FAIL'):
        print(__doc__); sys.exit(2)
    gate, target, result = args[0], args[1], args[2]

    def _opt(key):
        if key in args:
            i = args.index(key)
            if i + 1 < len(args):
                return args[i + 1]
        return None
    by = _opt('--by')
    d = _opt('--detail')
    details = [d] if d else None
    p = gatelib.write_report(gate, target, result, details=details, by=by)
    print(f"✓ 门报告写入 {os.path.relpath(p, gatelib.ROOT)}  [{gate}]={result}")
    sys.exit(0 if result == 'PASS' else 1)


if __name__ == '__main__':
    main()
