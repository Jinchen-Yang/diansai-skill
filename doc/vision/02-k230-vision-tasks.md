# K230 CanMV 视觉任务实战（巡线 / 色块 / AprilTag / 二维码 / 数字）

> 运行时 = CanMV 固件（MicroPython）。视觉 API 来自 `image` 模块；摄像头/显示来自 `media.sensor` / `media.display` / `media.media`。
> 传统视觉（巡线/色块/Tag/二维码）走 CPU 算子，零模型、即写即跑；数字/字符识别走 KPU + kmodel。
> 平台基础见 `01-k230-canmv.md`，结果怎么发给主控见 `03-uart-to-mcu.md`。

## 0. 通用骨架（先记死，各任务只换循环体）

```python
import time, os, sys
from media.sensor import *
from media.display import *
from media.media import *

sensor = Sensor()
sensor.reset()
sensor.set_framesize(width=640, height=480)   # 低分辨率=高帧率，循迹够用
sensor.set_pixformat(Sensor.RGB565)           # 彩色任务；巡线/Tag/二维码可用 Sensor.GRAYSCALE

Display.init(Display.ST7701, to_ide=True)      # 板载屏 + IDE 同时回显（上车可不显示省帧率）
MediaManager.init()                            # 必须在 sensor.run() 之前！
sensor.run()

clock = time.clock()
while True:
    clock.tick()
    img = sensor.snapshot()                    # 取一帧
    # ====== 任务处理写这里 ======
    Display.show_image(img)
    print(clock.fps())                         # 盯帧率
```

要点：
- `MediaManager.init()` **必须在 `sensor.run()` 之前**，顺序错会黑屏/报错。
- 像素格式：彩色识别（色块）用 `Sensor.RGB565`；巡线/AprilTag/二维码切 `Sensor.GRAYSCALE` 省算力更稳。
- 上车时**通常不显示**（省帧率），只把偏差/坐标经 UART 发给 MCU；**视觉端不做控制决策**。

## 1. 巡线 / 循迹（get_regression 线性回归求中线）

灰度阈值二值化 → `img.get_regression()` 对命中像素做最小二乘/鲁棒拟合出直线 → 用角度/中点算偏差。

```python
GRAYSCALE_THRESHOLD = [(0, 60)]   # 黑线白底→取低灰度段(min,max)，0~255

img = sensor.snapshot()                       # 建议 GRAYSCALE
line = img.get_regression(GRAYSCALE_THRESHOLD, robust=True)
if line:
    img.draw_line(line.line(), color=127, thickness=2)
    theta = line.theta()        # 直线角度 0~179°，判弯道方向
    rho   = line.rho()          # 原点到直线距离
    mag   = line.magnitude()    # 拟合质量/置信度，越大越可靠 → 做有效性/丢线判定
    x1,y1,x2,y2 = line.line()   # 两端点
```

偏差计算（喂转向 PID），常见两法：
```python
img_cx = img.width() // 2

# 法A：取回归线在前瞻行 y 的交点 x，做 中线x - 图像中心x
y_look = img.height() - 1
if x2 != x1:
    k = (y2 - y1) / (x2 - x1)
    line_x = x1 + (y_look - y1) / k if k != 0 else (x1 + x2)//2
else:
    line_x = x1
err = line_x - img_cx           # >0 偏右需左转；<0 偏左需右转 → PID

# 法B（更简）：用 theta 偏离 90° 的量作转向量；magnitude 太小判丢线→进入找线/停车状态机
```

实战提醒：
- `robust=True` 用 Theil-Sen（斜率中位数），抗噪/抗断线，但像素多时较慢；干净场景可关掉用最小二乘更快。
- 用 `magnitude()` 阈值做**丢线判定**。
- 灰度阈值用 CanMV IDE 直方图/阈值编辑器现场标定；光照变化大时先 `img.binary()` 再回归。
- 进阶**分段中线法**：图像按行分段，每行找黑线中点，多行中点拟合中线，更稳。

## 2. 色块识别（find_blobs + LAB 阈值）

CanMV 内部把 RGB565 转 LAB 后按阈值做连通域。每种颜色 = 一个 **LAB 6 元组**：
`(L_min, L_max, A_min, A_max, B_min, B_max)`，L∈[0,100]，A 绿(-)↔红(+)，B 蓝(-)↔黄(+)，均 [-128,127]。

```python
thresholds = [(30, 100,  15, 127,  15, 127),   # 红（用 IDE 阈值编辑器实测替换）
              (30, 100, -64,  -8,  50,  70),    # 绿
              (0,   40,   0,  90, -128, -20)]   # 蓝

img = sensor.snapshot()                          # RGB565
blobs = img.find_blobs([thresholds[0]],          # 传"阈值列表"，可一次传多组
                       area_threshold=10,        # 外接矩形面积下限，滤小框
                       pixels_threshold=10,      # 实际命中像素下限，滤稀疏噪点
                       merge=False,              # 是否合并重叠 blob
                       margin=0)                 # merge 时合并间距容差
if blobs:
    b = max(blobs, key=lambda x: x.pixels())     # 取最大块
    img.draw_rectangle(b.rect(), thickness=2)
    img.draw_cross(b.cx(), b.cy(), thickness=2)
    cx, cy = b.cx(), b.cy()                       # → 发给 MCU
```

blob 关键属性：

| 方法 | 含义 |
|---|---|
| `b.rect()` | 外接矩形 (x,y,w,h) |
| `b.cx()` / `b.cy()` | 质心坐标 |
| `b.pixels()` | 实际命中像素数 |
| `b.area()` | 外接矩形面积 |
| `b.code()` / `b.count()` | 命中哪个/几个阈值（多颜色区分） |

参数辨析：`pixels_threshold`（真实着色像素下限，抗稀疏）与 `area_threshold`（外框面积下限，抗小框）一起用最稳；`merge=True`+`margin` 把同色碎块合成大块（适合反光不连续）。
取阈值：CanMV IDE → **工具 → 机器视觉 → 阈值编辑器（Threshold Editor）**，拖滑块框住目标颜色直接复制 6 元组。**LAB 比 RGB 抗光照**，现场首选。

## 3. AprilTag（find_apriltags，TAG36H11）

电赛定位/标靶首选，**不需要镜头畸变校正**（与二维码不同）。

```python
img = sensor.snapshot()                          # GRAYSCALE 即可，更快
for tag in img.find_apriltags(families=image.TAG36H11):
    img.draw_rectangle(tag.rect(), color=(255,0,0), thickness=2)
    img.draw_cross(tag.cx(), tag.cy())
    print("id=%d cx=%d cy=%d rot=%.2f" % (tag.id(), tag.cx(), tag.cy(), tag.rotation()))
```

- 签名：`img.find_apriltags([roi[, families=image.TAG36H11[, fx,fy,cx,cy]]])`。
- TAG36H11 共 587 个 ID（0~586），官方推荐、最鲁棒；一次可识别多个家族。
- 属性：`id()`、`cx()/cy()`、`rotation()`（弧度，朝向）、`rect()`；传入相机内参 `fx,fy,cx,cy` 后还能给 3D 位姿（测距/对准）。
- **与二维码本质区别：AprilTag 无需 `lens_corr`，二维码强烈建议做畸变校正。**

## 4. 二维码 / 条码（find_qrcodes / find_barcodes + lens_corr）

```python
img = sensor.snapshot()                          # 二维码常用 GRAYSCALE
# 广角/鱼眼镜头先做桶形畸变校正，否则识别率大跌：
# img.lens_corr(strength=1.8, zoom=1.0)          # strength 按镜头实测调(1.0~2.0)

for code in img.find_qrcodes():
    img.draw_rectangle(code.rect(), thickness=2)
    print(code.payload())                        # 解码字符串（核心：取目标编号/指令）

for bar in img.find_barcodes():                  # 一维码
    print(bar.payload(), bar.type())
```

- `code.payload()` 取内容；`find_barcodes` 支持 EAN/UPC/CODE39/93/128/ISBN/PDF417 等几乎所有一维码。
- **`lens_corr` 仅二维码/条码需要**（去桶形畸变让码变平）；AprilTag 不用。`strength` 现场对着已知码微调到框正。
- 用 `Sensor.GRAYSCALE` 比 RGB565 更快更稳。

## 5. 数字 / 字符识别（模板匹配 vs KPU/YOLO）

| 路线 | 做法 | 适用 | 代价 |
|---|---|---|---|
| **模板匹配** `find_template` | 灰度 NCC 匹配预存模板 | 字体/大小/角度固定的少量数字 | 零训练，对旋转/缩放/光照敏感 |
| **AICube 零代码 + KPU** | AICube 平台标注→训练→导出 kmodel，板上 KPU 跑 | 印刷数字/简单字符要稳 | 需训练但无需写代码 |
| **YOLO + nncase** | 自训 YOLOv5/v8/11 → pt→onnx→kmodel | 复杂数字/多类/检测定位 | 训练 + 转换 |

模板匹配（最轻量）：
```python
import image
tmpl = image.Image("/sdcard/num8.bmp")           # 预存灰度模板
img = sensor.snapshot()                           # GRAYSCALE
r = img.find_template(tmpl, 0.70, step=4, search=image.SEARCH_EX)  # 0.70=相似度阈值
if r:
    img.draw_rectangle(r, thickness=2)            # r=(x,y,w,h) 命中位置
```

YOLO 模块 API（CanMV 封装，支持 YOLOv5/v8/11，分类/检测/分割/OBB）：
```python
from libs.YOLO import YOLOv8
yolo = YOLOv8(task_type="detect", mode="video",
              kmodel_path="/sdcard/digit.kmodel",
              labels=["0","1","2","3"],
              model_input_size=[320,320],          # 必须等于训练分辨率
              rgb888p_size=[640,480],
              conf_thresh=0.5, nms_thresh=0.45)
yolo.config_preprocess()
while True:
    img = sensor.snapshot()
    res = yolo.run(img)                            # detect→[box,score,cls] 列表
    yolo.draw_result(res, img)
    Display.show_image(img)
```

**关键坑（版本必须匹配）**：
- **nncase 转换器版本必须与板上 CanMV 固件版本对应**，否则 kmodel 加载失败/算子不支持。先确认固件版本再装对应 nncase。
- `model_input_size` 必须等于训练输入尺寸。
- 不会训模型用嘉楠 **AICube** 零代码平台（标注→训练→导出 kmodel），电赛推荐 **YOLOv8n**（v8s 易掉帧）。

## 6. 任务速查表（给小车）

| 任务 | API | 像素格式 | 输出给 MCU | 需畸变校正 |
|---|---|---|---|---|
| 巡线 | `get_regression` | GRAYSCALE | 偏差 err / theta | 否 |
| 找色块 | `find_blobs` | RGB565 | cx,cy / 颜色码 | 否 |
| 定位标靶 | `find_apriltags` | GRAYSCALE | id, cx, cy, rotation | **否** |
| 读指令码 | `find_qrcodes`/`find_barcodes` | GRAYSCALE | payload | **是（lens_corr）** |
| 认数字 | `find_template` / YOLO kmodel | GRAY / RGB888 | 类别 + 位置 | 否 |

落地建议：现场少显示、多看 `clock.fps()`；阈值/模板全部用 CanMV IDE 阈值编辑器现场标定；视觉结果统一打包成 `contracts/protocol` 的 UART 帧发给 MCU。

## 关键要点（速记）

- 通用骨架：`MediaManager.init()` 必须在 `sensor.run()` 前；彩色用 RGB565，巡线/Tag/二维码用 GRAYSCALE 省算力。
- 巡线：`get_regression(robust=True)` 取 theta/rho/magnitude，偏差 = 中线x − 图像中心x；magnitude 低判丢线。
- 色块：`find_blobs` 传 LAB 6 元组列表，IDE 阈值编辑器取值；pixels_threshold + area_threshold 双滤噪；取最大块的 cx/cy。
- AprilTag：`find_apriltags(families=image.TAG36H11)`，给 id/cx/cy/rotation，**无需畸变校正**，做定位标。
- 二维码：`find_qrcodes().payload()` 取内容，广角镜头先 `lens_corr`；条码 `find_barcodes`。
- 数字：固定场景用 `find_template`；要稳用 AICube 训 kmodel 或 YOLOv8n；**nncase 版本必须配固件**，input_size 配训练尺寸。

## 参考链接

- 官方 colortrack（色块）例程: https://www.kendryte.com/k230_canmv/main/zh/example/omv/colortrack.html
- 官方 AprilTags 例程: https://www.kendryte.com/k230_canmv/zh/v1.0/zh/example/omv/apriltages.html
- find_apriltags API/示例: https://developer.canaan-creative.com/k230_canmv/dev/zh/example/omv/April-Tags/find_apriltags.html
- 官方二维码识别例程: https://www.kendryte.com/k230_canmv/en/main/example/omv/qrcodes.html
- 带畸变校正二维码例程: https://www.kendryte.com/canmv/main/canmv/demo/16-Codes/qrcodes_with_lens_corr.html
- YOLO 模块 API 手册（中）: https://developer.canaan-creative.com/k230_canmv/zh/dev/zh/api/aidemo/YOLO%20%E6%A8%A1%E5%9D%97%20API%20%E6%89%8B%E5%86%8C.html
- YOLOv8 检测示例: https://www.kendryte.com/k230_canmv/zh/main/zh/example/ai/yolov8n_detection.html
- AI 开发文档（模型转换/部署）: https://www.kendryte.com/k230_canmv/zh/v1.3/zh/ai_dev_doc.html
- 01Studio 单色识别例程: https://wiki.01studio.cc/en/docs/canmv_k230/machine_vision/color_recognition/single_color/
- 01Studio AprilTag / 二维码 / 条码: https://wiki.01studio.cc/en/docs/canmv_k230/machine_vision/code/apriltag/
- DFRobot 巡线/线性回归教程: https://makelog.dfrobot.com.cn/article-318521.html
- CSDN《CanMV K230 快速线性回归（巡线）》: https://blog.csdn.net/weixin_45020839/article/details/141959258
- CSDN《K230 色块追踪 blobs 全面详解》: https://blog.csdn.net/weixin_64593595/article/details/144187093
- CSDN YOLO 部署实录（v8n / v11）: https://blog.csdn.net/2301_80029614/article/details/141473568 , https://blog.csdn.net/qq_61197032/article/details/144200967
