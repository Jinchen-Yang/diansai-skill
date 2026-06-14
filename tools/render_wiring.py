#!/usr/bin/env python3
"""接线图渲染：读 pinmap.yaml -> Graphviz DOT + Markdown 接线表（harness）。
有 `dot` 则同时渲 SVG；没有则只出 DOT + 表，并提示装 graphviz。

用法:
    python tools/render_wiring.py contracts/pinmap.yaml [out_prefix]
        out_prefix 默认 design/wiring  -> design/wiring.dot / .svg + design/harness.md
"""
import sys, os, shutil, subprocess, html
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def esc(s):
    return html.escape(str(s)).replace('|', '\\|')


def build_dot(pm):
    mcu = pm.get('mcu', 'MCU')
    assigns = pm.get('assignments', [])
    # 按 module 分组
    modules = {}
    for a in assigns:
        modules.setdefault(a.get('module', '?'), []).append(a)

    L = ['digraph wiring {', '  rankdir=LR;', '  node [fontname="monospace", fontsize=10];',
         '  edge [fontname="monospace", fontsize=9];', '']
    # MCU record 节点（左）
    pin_rows = ''.join(f'<tr><td port="{esc(a["signal"])}" align="left">{esc(a["pin"])}:{esc(a["function"])}'
                       f' ({esc(a["signal"])})</td></tr>' for a in assigns)
    L.append(f'  mcu [shape=plaintext, label=<<table border="1" cellborder="0" cellspacing="0">'
             f'<tr><td bgcolor="lightgrey"><b>{esc(mcu)}</b></td></tr>{pin_rows}</table>>];')
    # 模块节点（右）+ 边
    for mod, items in modules.items():
        mid = 'm_' + ''.join(ch if ch.isalnum() else '_' for ch in str(mod))
        net_rows = ''.join(f'<tr><td port="{esc(it["signal"])}" align="left">{esc(it.get("net","?"))}</td></tr>'
                           for it in items)
        L.append(f'  {mid} [shape=plaintext, label=<<table border="1" cellborder="0" cellspacing="0">'
                 f'<tr><td bgcolor="lightyellow"><b>{esc(mod)}</b></td></tr>{net_rows}</table>>];')
        for it in items:
            L.append(f'  mcu:"{esc(it["signal"])}" -> {mid}:"{esc(it["signal"])}" [label="{esc(it["function"])}"];')
    L.append('}')
    return '\n'.join(L)


def build_harness_md(pm):
    mcu = pm.get('mcu', 'MCU')
    L = [f'# 接线表 (harness) —— {mcu}', '',
         '> 由 tools/render_wiring.py 从 contracts/pinmap.yaml 生成。照此连线；连完逐行打勾。', '',
         '| ✓ | MCU 引脚 | 功能 | 外设 | 模块 | 对端引脚 | 备注 |',
         '|---|---|---|---|---|---|---|']
    for a in pm.get('assignments', []):
        L.append(f"| ☐ | {a.get('pin','')} | {a.get('function','')} | {a.get('peripheral','')} "
                 f"| {a.get('module','')} | {a.get('net','')} | {a.get('note','')} |")
    L += ['', '## 接线铁律', '- K230↔MCU 串口 **TX↔RX 交叉，必须共地**（见 contracts/protocol）。',
          '- 舵机/电机用**独立电源轨**，勿挂 3.3V 逻辑轨（见 design/power）。',
          '- 上电先量各轨电压，再插模块。']
    return '\n'.join(L)


def main():
    if len(sys.argv) < 2:
        print("用法: python tools/render_wiring.py <pinmap.yaml> [out_prefix]")
        sys.exit(2)
    pm = load(sys.argv[1])
    out_prefix = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'design', 'wiring')
    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)

    dot = build_dot(pm)
    dot_path = out_prefix + '.dot'
    with open(dot_path, 'w', encoding='utf-8') as f:
        f.write(dot)
    harness_path = os.path.join(os.path.dirname(out_prefix), 'harness.md')
    with open(harness_path, 'w', encoding='utf-8') as f:
        f.write(build_harness_md(pm))

    print(f"  -> {os.path.relpath(dot_path, ROOT)}")
    print(f"  -> {os.path.relpath(harness_path, ROOT)}")

    if shutil.which('dot'):
        svg_path = out_prefix + '.svg'
        try:
            subprocess.run(['dot', '-Tsvg', dot_path, '-o', svg_path], check=True)
            print(f"  -> {os.path.relpath(svg_path, ROOT)} (Graphviz 渲染)")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠ dot 渲染失败: {e}; 已留 .dot")
    else:
        print("  ⚠ 未装 graphviz(dot)：已输出 .dot 文本，可 'brew install graphviz' 后 "
              f"`dot -Tsvg {os.path.relpath(dot_path, ROOT)} -o {os.path.relpath(out_prefix,ROOT)}.svg`")
    print(f"✓ 接线图 + 接线表已生成（{len(pm.get('assignments',[]))} 条网络）。")


if __name__ == '__main__':
    main()
