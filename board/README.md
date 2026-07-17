# board/ —— git 背书的任务板（自动交接）

三个 lane（lead/硬件/控制/算法）各一台机器、各一个会话，**只能靠 git 协同**。本目录把"谁干什么、干到哪、下一步派给谁"变成可提交、可拉取的文件。

## 怎么用
- 看/领任务：跑 `/board`（或 `python tools/board.py list --lane <你的lane>`）。
- 干完：`python tools/board.py done <id> --by <你的lane>` —— **自动按流水线 DAG 给下游 lane 派生任务**。
- 近实时盯：`/loop 5m /board` 或 `sh tools/watch.sh <lane> 300`。
- 全局：`python tools/board.py status`。

## 机制
- 一任务一文件 `board/<id>.yaml`（避免 git 冲突）；`messages.md` 可追加跨 lane 留言。
- 任务只有**依赖全部 done** 才"就绪"；完成一个会派生把它列为依赖的下游任务。
- DAG 固定在 `tools/board.py` 的 `TASKS`（read-problem→方案→{环境,选材,视觉骨架}→供电→接线→{硬件连线,固件,测试清单}→bring-up→整车联调），lead 维护。

## 限制（诚实）
- 跨机器**只有 pull，没有 push 通知**：别人要 `git pull` 才看到你派的活（故有轮询）。
- 协作式：结构让交接显式可审计，但不强制；同机/同会话内可用后台通知做到秒级。

> `messages.md` 与本 README 跟踪入库；`<id>.yaml` 随进度变化提交。本机 lane 记在根目录 `.elec-lane`（不入库）。
