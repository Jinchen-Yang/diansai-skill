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

step "9) 任务板 DAG + 门-状态耦合（临时板/临时 design，不动真实目录）"
TB=/tmp/elec_board_test; TD=/tmp/elec_design_test
rm -rf "$TB" "$TD"; mkdir -p "$TB" "$TD"
export ELEC_BOARD_DIR="$TB" ELEC_DESIGN_DIR="$TD"
python3 tools/board.py init >/dev/null 2>&1
python3 tools/board.py done read-problem --by lead >/dev/null 2>&1
# plan-solution 带 signoff：未签字应被拒（门-状态生效）
if python3 tools/board.py done plan-solution --by lead >/dev/null 2>&1; then
  echo "  ✗ 门-状态失效：未签字竟能标完成"; fail=1
else
  echo "  ✓ 未签字被拒（board.py done 校验签字）"
fi
python3 tools/signoff.py approve solution-signoff --by lead >/dev/null 2>&1
if python3 tools/board.py done plan-solution --by lead >/dev/null 2>&1 && [ -f "$TB/vision-scaffold.yaml" ]; then
  echo "  ✓ 签字后放行 + 按 DAG 自动派生下游（vision-scaffold 等）"
else
  echo "  ✗ 签字后仍未放行/未派活"; fail=1
fi
unset ELEC_BOARD_DIR ELEC_DESIGN_DIR
rm -rf "$TB" "$TD"

step "10) 确定性门 --report 写机读报告 + gate_check 任务级校验"
TD=/tmp/elec_gate_test; rm -rf "$TD"; mkdir -p "$TD"
export ELEC_DESIGN_DIR="$TD"
python3 tools/pinmux_check.py contracts/pinmap.example.yaml --report --by lead >/dev/null 2>&1
python3 tools/signoff.py approve wiring-net-review --by lead >/dev/null 2>&1
if [ -f "$TD/gates/pinmux.yaml" ] && python3 tools/gate_check.py interconnect >/dev/null 2>&1; then
  echo "  ✓ pinmux 门报告落盘(PASS)，gate_check interconnect 通过（门+签字齐）"
else
  echo "  ✗ 门报告/任务级校验异常"; fail=1
fi
# 缺签字时 gate_check 应失败
TD2=/tmp/elec_gate_test2; rm -rf "$TD2"; mkdir -p "$TD2"
ELEC_DESIGN_DIR="$TD2" python3 tools/pinmux_check.py contracts/pinmap.example.yaml --report >/dev/null 2>&1
if ELEC_DESIGN_DIR="$TD2" python3 tools/gate_check.py interconnect >/dev/null 2>&1; then
  echo "  ✗ 缺签字竟通过 gate_check"; fail=1
else
  echo "  ✓ 门 PASS 但缺签字 → gate_check 正确拒绝"
fi
unset ELEC_DESIGN_DIR; rm -rf "$TD" "$TD2"

step "11) 目录归属强制（check_ownership）"
[ -f .elec-lane ] && mv .elec-lane .elec-lane.bak
echo 控制 > .elec-lane
viol=1; ok2=1; ok3=1
python3 tools/check_ownership.py --files contracts/x.yaml >/dev/null 2>&1 && viol=0   # 应越界->exit1
python3 tools/check_ownership.py --files firmware/x.c board/y.yaml STATUS.md >/dev/null 2>&1 || ok2=0
# gates/signoffs 是共享协同状态：控制 lane 写自己的 compile 门报告应放行
python3 tools/check_ownership.py --files design/gates/compile.yaml design/signoffs.yaml >/dev/null 2>&1 || ok3=0
rm -f .elec-lane
[ -f .elec-lane.bak ] && mv .elec-lane.bak .elec-lane
if [ "$viol" = 1 ] && [ "$ok2" = 1 ] && [ "$ok3" = 1 ]; then
  echo "  ✓ 越界写(contracts/)被拒；合规写(firmware/+board/)与共享门(design/gates/)放行"
else
  echo "  ✗ 归属强制异常 (viol=$viol ok2=$ok2 ok3=$ok3)"; fail=1
fi

printf "\n"
if [ "$fail" = 0 ]; then echo "✅ 全部自测通过"; else echo "❌ 有失败项"; exit 1; fi
