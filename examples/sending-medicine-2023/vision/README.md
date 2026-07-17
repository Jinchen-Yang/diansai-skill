# vision/ —— K230 视觉（算法 lane，CanMV）

## 运行
1. 按 `env/vision.md` 装 CanMV IDE + **锁定的 K230 镜像版本**（三人一致）。
2. 把本目录拷到 K230，`main.py` 为入口。
3. 串口波特 115200，与 `contracts/protocol` 一致；TX↔RX 交叉、共地。

## 文件
- `main.py` 主循环：取流 → 调 line_follow/blob_track/digit_recog → 用 `protocol.py` 发帧。
- `line_follow.py` 巡线偏差 · `blob_track.py` 色块 · `digit_recog.py` 数字（连续N帧采信）。
- `config.py` ★ 阈值/ROI/曝光/串口——**现场标定改这里**。
- `protocol.py` 从 `contracts/` 复制，**勿手改**（改协议找 lead 改 protocol.yaml 重生成）。

## 现场标定（见 design/test_plan.md）
灰度阈值、ROI、曝光、色块 LAB、数字模型——都随光照/赛道变，现场标。
