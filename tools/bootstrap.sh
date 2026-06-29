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

# 启用提交前兜底门（文件归属 + 契约门），见 .githooks/pre-commit
if [ -d "$HERE/.git" ] || git -C "$HERE" rev-parse --git-dir >/dev/null 2>&1; then
  chmod +x "$HERE/.githooks/pre-commit" 2>/dev/null || true
  git -C "$HERE" config core.hooksPath .githooks
  echo "git hooks 已启用（core.hooksPath=.githooks）。"
fi

# 本机 lane（用于归属校验）；已存在则不动
if [ ! -f "$HERE/.elec-lane" ]; then
  echo "提示：建 .elec-lane 写本机 lane（lead/硬件/控制/算法），例: echo 控制 > .elec-lane"
fi
echo "host env ready."
