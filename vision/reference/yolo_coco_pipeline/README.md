# 参考代码：KPU YOLOv8 COCO 目标检测

## 写代码前先学

先在 CanMV IDE 中运行并确认亚博官方例程：

1. `09.Scene/03.object_detect_yolov8n.py`
2. `14.export/CanmvIDE-K230/14.object_detect_yolov8n.py`

重点理解四段链路：`PipeLine.get_frame()` 取帧，`Ai2d` 做 letterbox 预处理，`AIBase.run()` 调用 KPU 推理，`aidemo.yolov8_det_postprocess()` 将模型输出转换为检测框。

## 本模块做什么

`main.py` 是从官方例程整理出的独立可运行版本。它：

- 加载板内的 `/sdcard/kmodel/yolov8n_224.kmodel`。
- 识别 COCO 80 类日常物体，在 LCD/IDE 画面标出类别、置信度和框。
- 将每帧结果归一为 `label`、`score`、`x`、`y`、`w`、`h`、`cx`、`cy`，并低频打印到 IDE 控制台。
- 当前不导入 `YbUart`、不初始化 UART，也不向主控发送任何数据。

它用于学习 KPU 模型部署和验证板卡链路，不等价于电赛目标识别方案。COCO 模型不认识特定靶标、赛题数字或自定义图案。

## 保留原因

它不在 `vision/demos/`，不作为电赛可直接使用的能力。保留仅用于查阅固定 COCO YOLOv8 的 KPU 管线；自定义电赛目标应使用 `demos/10_online_training_deploy/` 的在线训练部署链路。

## 运行方法

1. 在 CanMV IDE 中打开本目录的 `main.py`，直接运行。
2. 用 `person`、`cup`、`bottle`、`cell phone` 等 COCO 常见类别测试。
3. 观察类别是否正确、框是否跟随目标，以及 IDE 控制台的 `yolo count=...` 输出。

若报模型文件找不到，先确认 SD 卡上存在 `/sdcard/kmodel/yolov8n_224.kmodel`。不要先复制其他格式的 ONNX、PT 或任意 `.kmodel` 文件替换。

## 现场标定参数（比赛时必看）

| 参数 | 含义 | 什么时候调 |
| --- | --- | --- |
| `KMODEL_PATH` | 当前 KPU 模型文件路径 | 切换到已验证、与板端固件兼容的模型时才改。模型改变后必须同步检查类别表、输入尺寸和后处理。 |
| `CONFIDENCE_THRESHOLD` | 最低置信度，低于该值的框丢弃 | 误检多时逐步提高；漏检多时逐步降低。初始值为 0.30。 |
| `NMS_THRESHOLD` | 同类重叠框的抑制阈值 | 同一目标反复出现重叠框时调低；相邻不同目标被合并时调高。初始值为 0.40。 |
| `ALLOWED_LABELS` | 允许显示的类别白名单 | 赛题只需要少数已支持类别时填写，减少无关检测框；空元组表示全部显示。 |
| `MAX_BOXES_NUM` | 单帧保留的最多检测框数 | 复杂背景框太多影响调试时调低；通常保持 30。 |
| `AI_FRAME_SIZE` | 送入 AI 管线的相机图像尺寸 | 本官方模型固定使用 `[224, 224]`；不要为了提高分辨率直接改动。 |

调试顺序：先确认模型与类别表匹配 -> 固定相机位置、距离和光照 -> 用已知 COCO 物体验证类别 -> 调 `CONFIDENCE_THRESHOLD` -> 再调 `NMS_THRESHOLD` -> 最后使用 `ALLOWED_LABELS` 限制任务类别。只有屏幕结果稳定后，才设计 UART 回传与主控动作。

## 更换为电赛模型时的要求

不能只把 `KMODEL_PATH` 改成新文件。必须同时确认：

1. 新模型的输入尺寸和颜色/张量格式。
2. 模型类别顺序，并用其替换 `COCO_LABELS`。
3. 模型是否仍是本文件对应的 YOLOv8 检测输出；若不是，`postprocess()` 必须按实际模型重写。
4. 在本板、当前 CanMV 固件和实际赛场光照下完成实物测试。

## 实测状态

亚博官方 COCO YOLO 示例已由操作者确认“差不多可信”。本仓库整理版尚未做独立实机回归；运行本文件并确认类别、框和帧率后，再将状态更新为“实机通过”。
