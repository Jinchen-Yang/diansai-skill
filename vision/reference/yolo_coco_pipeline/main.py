"""
第 8 模块：YOLOv8 COCO 目标检测。

基于亚博智能 09.Scene/03.object_detect_yolov8n.py 整理。
本程序仅在屏幕和 IDE 控制台调试，不初始化 UART，也不向主控发送数据。
"""

import gc

import aidemo
import nncase_runtime as nn
import ulab.numpy as np

from libs.AI2D import Ai2d
from libs.AIBase import AIBase
from libs.PipeLine import PipeLine, ScopedTiming
from libs.Utils import ALIGN_UP, get_colors, letterbox_pad_param


# ============================= 现场标定区 =============================
# 板内预装的官方 COCO YOLOv8n 模型。路径不存在时，不能运行本程序。
KMODEL_PATH = "/sdcard/kmodel/yolov8n_224.kmodel"
MODEL_INPUT_SIZE = [224, 224]

# 该模型按 224 x 224 图像推理；不要为提高画质而随意改成相机原始分辨率。
AI_FRAME_SIZE = [224, 224]
DISPLAY_MODE = "lcd"
DISPLAY_SIZE = [640, 480]

# 分数低于此值的候选框直接丢弃。先从 0.30 开始现场调整。
CONFIDENCE_THRESHOLD = 0.30
# 两个框重叠较大时，NMS 保留分数更高的一个。先保持官方值 0.40。
NMS_THRESHOLD = 0.40
# 单帧允许输出的最多目标数，避免复杂场景输出过多框。
MAX_BOXES_NUM = 30

# 空元组表示显示全部 COCO 类。填写如 ("person", "cup") 时只显示这些类别。
ALLOWED_LABELS = ()
# 控制台每隔多少帧输出一次结果；只影响调试输出，不影响检测。
PRINT_PERIOD_FRAMES = 20


COCO_LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
    "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant",
    "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard",
    "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush",
]


class YoloV8CocoApp(AIBase):
    """封装官方 YOLOv8n 模型的预处理、推理后处理与屏幕绘制。"""

    def __init__(self):
        """使用当前模块顶部的现场标定参数创建推理对象。"""
        super().__init__(KMODEL_PATH, MODEL_INPUT_SIZE, AI_FRAME_SIZE, 0)
        self.ai_frame_size = [ALIGN_UP(AI_FRAME_SIZE[0], 16), AI_FRAME_SIZE[1]]
        self.display_size = [ALIGN_UP(DISPLAY_SIZE[0], 16), DISPLAY_SIZE[1]]
        self.colors = get_colors(len(COCO_LABELS))

        # 模型输入和输出均为 NCHW 的 uint8 数据，保持亚博官方例程的格式。
        self.ai2d = Ai2d(0)
        self.ai2d.set_ai2d_dtype(
            nn.ai2d_format.NCHW_FMT,
            nn.ai2d_format.NCHW_FMT,
            np.uint8,
            np.uint8,
        )

    def config_preprocess(self):
        """构建等比例 letterbox 填充和缩放链路，不能改为直接拉伸。"""
        top, bottom, left, right, _ = letterbox_pad_param(
            self.ai_frame_size, MODEL_INPUT_SIZE
        )
        self.ai2d.pad([0, 0, 0, 0, top, bottom, left, right], 0, [128, 128, 128])
        self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
        self.ai2d.build(
            [1, 3, self.ai_frame_size[1], self.ai_frame_size[0]],
            [1, 3, MODEL_INPUT_SIZE[1], MODEL_INPUT_SIZE[0]],
        )

    def preprocess(self, frame_np):
        """把 PipeLine 给出的当前帧交给 KPU；AIBase 会执行已构建的 ai2d。"""
        return [nn.from_numpy(frame_np)]

    def postprocess(self, results):
        """将 YOLOv8 输出解码为框、类别索引和置信度三个列表。"""
        output = results[0][0].transpose()
        return aidemo.yolov8_det_postprocess(
            output.copy(),
            [self.ai_frame_size[1], self.ai_frame_size[0]],
            [MODEL_INPUT_SIZE[1], MODEL_INPUT_SIZE[0]],
            [self.display_size[1], self.display_size[0]],
            len(COCO_LABELS),
            CONFIDENCE_THRESHOLD,
            NMS_THRESHOLD,
            MAX_BOXES_NUM,
        )

    def normalize_results(self, dets):
        """过滤类别并转换为后续协议可复用的字典结果。"""
        normalized = []
        if not dets:
            return normalized

        for index in range(len(dets[0])):
            label_index = int(dets[1][index])
            label = COCO_LABELS[label_index]
            if ALLOWED_LABELS and label not in ALLOWED_LABELS:
                continue

            x, y, width, height = [int(round(value, 0)) for value in dets[0][index]]
            normalized.append({
                "label": label,
                "score": round(float(dets[2][index]), 3),
                "x": x,
                "y": y,
                "w": width,
                "h": height,
                "cx": x + width // 2,
                "cy": y + height // 2,
            })
        return normalized

    def draw_results(self, pipeline, results):
        """清除旧 OSD 后绘制当前帧的所有检测框和标签。"""
        pipeline.osd_img.clear()
        for result in results:
            label_index = COCO_LABELS.index(result["label"])
            color = self.colors[label_index]
            label_text = "%s %.2f" % (result["label"], result["score"])
            pipeline.osd_img.draw_rectangle(
                result["x"], result["y"], result["w"], result["h"],
                color=color,
                thickness=3,
            )
            pipeline.osd_img.draw_string_advanced(
                result["x"], max(0, result["y"] - 28), 20, label_text, color=color
            )


def main():
    """运行独立的 COCO YOLO 检测演示。"""
    pipeline = None
    detector = None
    frame_count = 0

    try:
        pipeline = PipeLine(
            rgb888p_size=AI_FRAME_SIZE,
            display_size=DISPLAY_SIZE,
            display_mode=DISPLAY_MODE,
        )
        pipeline.create()

        detector = YoloV8CocoApp()
        detector.config_preprocess()

        while True:
            # PipeLine 的帧数据直接进入 AIBase，不把它命名为 image，避免遮蔽 image 模块。
            frame = pipeline.get_frame()
            with ScopedTiming("yolo total", 0):
                raw_detections = detector.run(frame)
                detections = detector.normalize_results(raw_detections)
                detector.draw_results(pipeline, detections)
                pipeline.show_image()

            frame_count += 1
            if frame_count % PRINT_PERIOD_FRAMES == 0:
                print("yolo count=%d results=%s" % (len(detections), detections))
            gc.collect()

    except KeyboardInterrupt:
        print("user stop")
    except BaseException as error:
        print("yolo error: %s" % error)
    finally:
        if detector is not None:
            detector.deinit()
        if pipeline is not None:
            pipeline.destroy()


main()
