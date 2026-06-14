#!/usr/bin/env sh
# 一键自测：所有确定性门 + 主机测试 + 跨语言一致性 + 语法检查。
# 用法: sh tools/selftest.sh   （在仓库任意处）
cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)
FW=examples/sending-medicine-2023/firmware
fail=0

step() { printf "\n=== %s ===\n" "$1"; }

step "1) 协议生成 + 两端一致性自检"
python3 tools/gen_protocol.py || fail=1

step "2) pinmux 门（样例应 PASS）"
python3 tools/pinmux_check.py contracts/pinmap.example.yaml || fail=1

step "3) 供电预算门（样例应 PASS，电机按堵转）"
python3 tools/power_budget.py examples/sending-medicine-2023/power.yaml || fail=1

step "4) 接线图渲染（DOT/harness，有 dot 则出 SVG）"
python3 tools/render_wiring.py contracts/pinmap.example.yaml examples/sending-medicine-2023/wiring || fail=1

step "5) 固件主机测试（PID/调度器/协议C端往返/坏校验拒收）"
cc -std=c11 -Wall -I"$FW/middleware" -Icontracts \
   "$FW/tests/host_test.c" "$FW/middleware/pid.c" "$FW/middleware/scheduler.c" \
   -o /tmp/elec_host_test && /tmp/elec_host_test || fail=1

step "6) 跨语言协议一致性（C 帧 == Python 帧）"
python3 tests/test_protocol_xlang.py || fail=1

step "7) 固件 driver/app 层语法检查"
for f in "$FW"/driver/*.c "$FW"/middleware/vofa.c "$FW"/app/*.c; do
  if cc -std=c11 -fsyntax-only -I"$FW/middleware" -I"$FW/driver" -Icontracts "$f"; then
    echo "  ✓ $f"
  else
    echo "  ✗ $f"; fail=1
  fi
done

step "8) K230 视觉脚本语法检查"
if python3 -m py_compile examples/sending-medicine-2023/vision/*.py; then
  echo "  ✓ vision py_compile"
else
  echo "  ✗ vision py_compile"; fail=1
fi

printf "\n"
if [ "$fail" = 0 ]; then echo "✅ 全部自测通过"; else echo "❌ 有失败项"; exit 1; fi
