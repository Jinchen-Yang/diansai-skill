#!/usr/bin/env python3
"""目录归属强制（确定性，无 LLM）——按本机 lane 校验本次改动没越界写别人目录。

归属铁律见 CLAUDE.md。本机 lane 取仓库根 `.elec-lane`（未跟踪文件，一行：lead/硬件/控制/算法）。
被 .githooks/pre-commit 调用做提交前兜底；也可手动跑。lead 视为超级用户（可写任何目录）。

用法:
    python tools/check_ownership.py                 # 校验 git 暂存区(staged)改动
    python tools/check_ownership.py --files a b c    # 校验指定文件
越界 -> exit 1；通过 / 无法判定 lane -> exit 0。
"""
import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 目录前缀 -> 允许写入的 lane 集合（lead 永远允许，单列在下方逻辑）。
OWN = {
    'design/':    {'硬件'},
    'firmware/':  {'控制'},
    'vision/':    {'算法'},
    'contracts/': set(),   # 只 lead
    'env/':       set(),
    'tools/':     set(),
    'lib/':       set(),
    '.claude/':   set(),
}
# 任何 lane 都可写（协同状态）：
SHARED = ('board/', 'STATUS.md', '.elec-lane', '.elec-mode')


def lane():
    p = os.path.join(ROOT, '.elec-lane')
    if not os.path.exists(p):
        return None
    return open(p, encoding='utf-8').read().strip()


def staged_files():
    out = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                         cwd=ROOT, capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f.strip()]


def violations(files, ln):
    bad = []
    for f in files:
        f = f.replace('\\', '/')
        if any(f == s or f.startswith(s) for s in SHARED):
            continue
        owner_prefix = next((p for p in OWN if f.startswith(p)), None)
        if owner_prefix is None:
            continue  # kb/、README、根治理文件等：人工维护，不拦
        allowed = OWN[owner_prefix]
        if ln not in allowed:
            who = '只 lead' if not allowed else ('lead/' + '/'.join(sorted(allowed)))
            bad.append((f, owner_prefix, who))
    return bad


def main():
    ln = lane()
    if ln is None:
        print("（未设 .elec-lane，跳过归属校验。建议各机写入本机 lane：echo 控制 > .elec-lane）")
        sys.exit(0)
    if ln == 'lead':
        sys.exit(0)  # lead 是超级用户，可写任何目录
    if '--files' in sys.argv:
        files = sys.argv[sys.argv.index('--files') + 1:]
    else:
        files = staged_files()
    bad = violations(files, ln)
    if not bad:
        sys.exit(0)
    print(f"✗ 归属越界（本机 lane = {ln}）——以下改动写到了不归你的目录：")
    for f, prefix, who in bad:
        print(f"   - {f}   （{prefix} 归 {who}）")
    print("  改法：只动自己 lane 的产物目录 + board/ + STATUS.md；契约/env/tools 由 lead 改。")
    print("  确需越过：git commit --no-verify（请先与 lead 沟通，避免 git 冲突）。")
    sys.exit(1)


if __name__ == '__main__':
    main()
