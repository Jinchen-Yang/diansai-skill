#!/usr/bin/env sh
# host 环境一键装：运行 .claude/skills 调用的本地工具所需（无 LLM 依赖）
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m pip install --user -r "$HERE/requirements.txt"
echo "checking optional graphviz(dot) ..."
if command -v dot >/dev/null 2>&1; then
  echo "  dot OK"
else
  echo "  dot 缺失：接线图渲染将退化为 DOT 文本。可 'brew install graphviz' 或 'apt install graphviz'。"
fi
echo "host env ready."
