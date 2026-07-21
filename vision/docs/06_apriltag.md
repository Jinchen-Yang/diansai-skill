# 第 6 模块：AprilTag 识别

## 写代码前先学

先在 CanMV IDE 中运行亚博源码：

1. `06.Codes/03.find_apriltag.py`
2. `14.export/CanmvIDE-K230/04.find_apriltag.py`

重点观察 `families` 位掩码，以及每个 Tag 对象的 `family()`、`id()`、`rect()`、`cx()`、`cy()` 和 `rotation()`。

## 本模块做什么

`demos/06_apriltag/main.py` 使用 RGB565、`400 x 240` 图像调用 `image.find_apriltags(families=TAG_FAMILIES)`。

每个检测结果会输出：

- `family`：Tag 家族名称。
- `id`：该家族中的编号。
- `cx`、`cy`：中心坐标。
- `x`、`y`、`w`、`h`：外接矩形。
- `rotation_deg`：旋转角度，单位为度。

画面中的所有 Tag 都会被标注。与亚博示例不同，本示例不会 `break`，因此可以同时观察多个 Tag。

## 现场标定参数（比赛时必看）

| 参数 | 含义 | 什么时候调 |
| --- | --- | --- |
| `TAG_FAMILIES` | 允许检测的 Tag 家族位掩码 | 先确认题目使用的家族，只保留需要的家族；家族不匹配时不会有结果。 |
| `FRAME_WIDTH` / `FRAME_HEIGHT` | 相机处理分辨率 | Tag 太小、漏检时可提高分辨率；帧率不足时再降低。必须保持显示比例一致。 |
| `PRINT_PERIOD_FRAMES` | IDE 控制台输出周期 | 只影响调试输出频率，不影响识别。 |
| `DISPLAY_WIDTH` / `DISPLAY_HEIGHT` | 显示画布尺寸 | 只在显示位置或缩放异常时调整，不参与识别。 |

调试顺序：先确认 Tag 家族 -> 固定相机高度和角度 -> 确认 Tag 完整入镜、光照均匀 -> 再调分辨率 -> 最后才考虑 UART 输出和主控动作。

## 实测状态

已使用实际 AprilTag 靶标验证通过。当前代码可稳定完成 Tag 检测、框选、中心坐标、ID 和旋转角输出；比赛时仍需根据题目使用的 Tag 家族、安装高度和光照重新确认 `TAG_FAMILIES` 与分辨率。

## 通过标准

- 单个 Tag 能稳定显示红色外框、绿色中心和正确 ID。
- Tag 旋转时 `rotation_deg` 的变化方向正确。
- 同时放入多个 Tag 时全部被处理。
- Tag 移出画面后 `APRILTAG=0`，不会继续使用上一帧结果。
