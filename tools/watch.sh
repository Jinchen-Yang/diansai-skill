#!/usr/bin/env sh
# 纯终端轮询：定时 git pull + 显示派给本 lane 的就绪任务（/board 的非 Claude 版）。
# 用法: sh tools/watch.sh <lane> [间隔秒=300]
#   lane ∈ lead | 硬件 | 控制 | 算法
LANE="$1"
INTERVAL="${2:-300}"
[ -z "$LANE" ] && { echo "用法: sh tools/watch.sh <lane> [间隔秒]"; exit 2; }
cd "$(dirname "$0")/.." || exit 1

echo "轮询任务板：lane=$LANE 间隔=${INTERVAL}s （Ctrl-C 退出）"
last=""
while true; do
  git pull --rebase --quiet 2>/dev/null
  cur="$(python3 tools/board.py list --lane "$LANE" 2>/dev/null)"
  if [ "$cur" != "$last" ]; then
    printf '\n[%s] 任务板更新:\n%s\n' "$(date '+%H:%M:%S')" "$cur"
    last="$cur"
  fi
  sleep "$INTERVAL"
done
