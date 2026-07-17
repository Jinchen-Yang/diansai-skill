# 第 3 模块：圆形检测

## 写代码前先学

在 CanMV IDE for K230 v4.0.7 先运行亚博源码中的：

1. 绘制图像中的“绘制圆形”。
2. `04.Detecting/03.find_circles.py`：`find_circles(threshold=...)` 的基础调用。
3. `06.cv_lite/3.grayscale_find_circles.py`：霍夫圆的 `minDist`、`param1`、`param2`、半径范围。
4. `06.cv_lite/4.rgb888_find_circles.py`：理解彩色图做圆检测的性能代价；本模块暂不使用它。

## 本模块逻辑

```text
取 RGB565 图像
  -> find_circles(阈值)
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
