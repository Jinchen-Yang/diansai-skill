# 色块/光点追踪：返回最大色块中心 (cx, cy) 或 None。阈值见 config.BLOB_THRESH（现场标）。

def find(img, cfg):
    if img is None:
        return None                    # 主机占位
    blobs = img.find_blobs(cfg.BLOB_THRESH, pixels_threshold=50,
                           area_threshold=50, merge=True)
    if not blobs:
        return None
    b = max(blobs, key=lambda x: x.pixels())
    return (b.cx(), b.cy())
