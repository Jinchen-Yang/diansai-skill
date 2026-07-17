# 第 4 模块：视觉巡线

## 写代码前先学

在 CanMV IDE for K230 v4.0.7 先运行亚博源码中的：

1. `05.Color/04.find_line.py`：基于 LAB 色块的基础巡线思路与下半画面 ROI。
2. `04.Detecting/05.linear_regression_fast.py`：直线拟合与边缘方案的概念；本模块不直接使用它。
3. `06.cv_lite/13.grayscale_threshold_binary.py`：理解二值化，观察阈值变化对黑白线条的影响。

## 本模块逻辑

```text
取 RGB565 图像
  -> 在近、中、远三条 ROI 内找黑色最大 blob
  -> 按 ROI 权重合成黑线横向中心
  -> error = 线中心 x - 画面中心 x
  -> 无有效 ROI 时 valid=0、error=0、显示 LINE LOST
```

所以约定为：黑线在画面右侧，`error > 0`；黑线在左侧，`error < 0`。未来和主控对接时只在 `valid=1` 时发送 `protocol.line_error(error)`；丢线必须单独通知主控，不能继续发上一帧旧误差。

## 运行与调参

1. 在白色硬纸板上贴约 18 至 25 mm 宽的黑色哑光胶带，先做直线，再做缓弯。
2. 将摄像头固定在车头预定高度和角度，避免手持测试后把阈值当作正式参数。
3. CanMV IDE 直接运行 `demos/04_line_follow/main.py`。
4. 调 `BLACK_LINE_THRESHOLD` 使胶带被检测而白底、阴影尽量不被检测。
5. 假线块多：提高 `MIN_AREA`，或缩小 `ROIS` 到赛道实际会出现的位置。
6. 缓弯时远处 ROI 丢失并不一定是故障；近处 ROI 能稳定得到线中心更重要。

## 通过标准

- 直线居中时 `error` 接近 0。
- 胶带移到画面右侧时 `error` 为正，左侧时为负。
- 用手遮住胶带时明确显示 `LINE LOST`，不会沿用旧误差。
- 缓弯时至少近处 ROI 能连续给出方向正确的误差。

后续联调模块会把此结果通过共享 `protocol.py` 发送给 MSPM0/STM32，并由主控负责 PID、速度和安全停车。
