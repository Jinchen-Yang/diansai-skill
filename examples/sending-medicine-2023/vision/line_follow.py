# 巡线：在 ROI 内求黑线中线，输出相对画面中心的偏差 error(int16)
# 偏差 = 中线 x - 画面中心 x；右偏为正。阈值/ROI 见 config.py（现场标）。

def line_error(img, cfg):
    if img is None:
        return 0                       # 主机占位
    x, y, w, h = cfg.ROI
    # 在 ROI 内找黑线 blob，取最大者质心 cx
    blobs = img.find_blobs([cfg.GRAY_THRESHOLD], roi=cfg.ROI,
                           pixels_threshold=20, area_threshold=20, merge=True)
    if not blobs:
        return None                    # 丢线：返回 None，主控保持上次/进丢线处理
    largest = max(blobs, key=lambda b: b.pixels())
    cx = largest.cx()
    center = x + w // 2
    return cx - center                 # int，发送时裁到 int16
