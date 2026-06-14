# host 环境（lead，跑 .claude/skills 的本地工具）

跑设计流水线工具（gen_protocol / pinmux_check / 后续 render_wiring 等）所需。**无 LLM 依赖。**

## 一键装

```sh
sh tools/bootstrap.sh        # 装 requirements.txt + 检查 graphviz
```

## 清单 / 自检

| 组件 | 版本 | 自检 |
|---|---|---|
| Python | 3.13.x | `python3 --version` |
| PyYAML | ≥6.0 | `python3 -c 'import yaml'` |
| requests | ≥2.28 | `python3 -c 'import requests'` |
| graphviz(dot) | 任意（Pass B 用） | `dot -V`；缺则接线图退化为 DOT 文本 |
| git | ≥2.30 | `git --version` |

## 验证流水线工具

```sh
python3 tools/gen_protocol.py                       # 应输出"两端一致"
python3 tools/pinmux_check.py contracts/pinmap.example.yaml   # 应 PASS
```
