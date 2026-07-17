# inputs/ — 每年的外部输入（用户投喂）

每届比赛把这两样**原始文档（PDF 或文本均可）**丢进来，由 skill 解析：

- `problem/` — **当年官方题目**（含限制条款/评分/场地/计时）。投喂后跑 `/read-problem`。
- `partslist/` — **主办方配件表**（可能用到的器件清单，统一采购的来源）。`/select-parts` 从中选材。

> 解析 PDF 属多模态任务，**只在 lead/Claude 会话跑**（见 CLAUDE.md 能力标注）。
> 解析产物落在 `design/`（problem.yaml / bom.csv 等），不要手改产物，改输入或重跑 skill。
