# 第 3 模块：圆形检测

## 写代码前先学

在 CanMV IDE for K230 v4.0.7 先运行亚博源码中的：

1. 绘制图像中的“绘制圆形”。
2. `04.Detecting/03.find_circles.py`：`find_circles(threshold=...)` 的基础调用。
3. `06.cv_lite/4.rgb888_find_circles.py`：本模块的默认实现，学习霍夫圆的 `minDist`、`param1`、`param2`、半径范围。
4. `06.cv_lite/3.grayscale_find_circles.py`：仅用于对比。其 16:9 输入被非等比缩放到 4:3 输出，会使圆变成竖向椭圆。

## 本模块逻辑

```text
取 RGB888 图像
  -> cv_lite.rgb888_find_circles(霍夫圆参数)
  -> 按半径过滤候选圆
  -> 选择最大圆
  -> 与上一帧比较圆心位置和半径
  -> 同一圆连续 3 帧才标记 STABLE
```

圆检测对圆弧、镜头反光、杯口、车轮、灯具边缘都可能有响应。它不限定黑色圆，检测依据是圆周边缘与背景的对比。`STABLE` 的意思是同一圆连续存在，不代表它一定就是赛题目标；题目识别还需要结合颜色、大小、位置或标记进一步筛选。

## 运行与调参

1. CanMV IDE 直接打开并运行 `demos/03_circle/main.py`。
2. 首先使用深色圆环或黑边白底圆靶，背景尽量无其他圆形物体。
3. 假圆多：提高 `CIRCLE_THRESHOLD`，缩小 `MIN_RADIUS`/`MAX_RADIUS` 的允许范围。
4. 真实圆漏检：先增加边缘对比、避免反光，再适度降低 `CIRCLE_THRESHOLD`。
5. 圆心跳动：先确认镜头和目标固定；若真实抖动范围较大，再小幅调大 `TRACK_CENTER_DELTA`。

画面中灰色细圈是底层 `find_circles()` 的原始候选，蓝色粗圈才是本程序筛选后的主圆。若 `raw=0`，说明应调边缘、光照或 `CIRCLE_THRESHOLD`；若 `raw>0` 但 `valid=0`，说明半径范围过滤过严，应调 `MIN_RADIUS`/`MAX_RADIUS`。

## 通过标准

- 主圆边框基本贴合目标圆边缘，圆心位置正确。
- 目标静止时，在 3 帧后显示 `STABLE`。
- 拿走目标或换到另一个位置较远的圆，稳定计数应重新开始。
- 调整目标远近后，半径变化方向正确。

通过后进入第 4 模块：巡线视觉。届时会把 ROI、阈值、误差输出和丢线判定组合成可交给主控 PID 的结果。

## 现场标定参数（比赛时必看）

| 参数 | 含义 | 什么时候调 |
| --- | --- | --- |
| `MIN_RADIUS` / `MAX_RADIUS` | 目标圆的半径允许范围（像素） | 跟据比赛目标在预定观测距离的大小先固定。 |
| `MIN_CENTER_DISTANCE` | 两个候选圆心的最小距离 | 同一个圆被重复报出时上调；靠近的真圆被合并时下调。 |
| `CANNY_HIGH_THRESHOLD` (`param1`) | 霍夫圆前的 Canny 高阈值 | 边缘噪声、反光引起假圆时上调；圆边缘很淡而漏检时下调。 |
| `ACCUMULATOR_THRESHOLD` (`param2`) | 霍夫累加器的确认阈值 | 假圆多时上调；真圆漏检时下调。 |
| `TRACK_CENTER_DELTA` / `TRACK_RADIUS_DELTA` | 同一圆在连续帧间的允许变化 | 目标或车辆有正常轻微抖动时小幅上调；不同圆被错当成同一目标时下调。 |
| `STABLE_FRAMES` | 确认主圆稳定需要的连续帧数 | 误触发时上调；响应过慢时下调。 |

调试顺序：先确认相机预览比例正确 -> 设定 `MIN_RADIUS` / `MAX_RADIUS` -> 调 `MIN_CENTER_DISTANCE` -> 调 `ACCUMULATOR_THRESHOLD` -> 必要时微调 `CANNY_HIGH_THRESHOLD` -> 最后调稳定参数。`HOUGH_DP` 继续保持 1，不作为现场首选调参。

## 实测选型记录

当前圆形模块的默认方案是 `06.cv_lite/4.rgb888_find_circles.py` 中的 `cv_lite.rgb888_find_circles()`。它以 `1280 x 960` 的 4:3 传感器模式输出 `640 x 480`，横纵缩放比例相同，画面不会被拉伸；并且已在本机实测中表现出更好的识别效果。

现在 `demos/03_circle/main.py` 已经直接替换为这个 CV Lite 实现，不再使用 `image.find_circles()`。因此以下的默认调参也从 `CIRCLE_THRESHOLD` 改为 `minDist`、`param1`、`param2` 与半径范围。

- 优先基线：`Sensor.RGB888` + `img.to_numpy_ref()` + `cv_lite.rgb888_find_circles()`
- 返回格式：`[x1, y1, r1, x2, y2, r2, ...]`，需按 3 个元素为一组遍历。
- 现场调参顺序：先限定 `minRadius` / `maxRadius`，再调 `minDist`，最后用 `param2` 控制假圆数量。`param1` 为 Canny 高阈值。
- 本文早先的 `find_circles()` 示例保留作为 CanMV 基础 API 对照与兜底，不再作为圆形赛题的默认实现。
