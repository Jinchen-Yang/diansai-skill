# 门牌数字识别：返回 (class_id, confidence) 或 None。
# 连续 DIGIT_STABLE_N 帧一致才采信（防误识，呼应主控 FSM）。KPU 模型/模板按现场替换。

_last, _streak = None, 0


def recognize(img, cfg):
    global _last, _streak
    if img is None:
        return None                    # 主机占位
    cls, conf = _infer(img, cfg)       # TODO: 接 KPU 模型推理
    if cls is None:
        _last, _streak = None, 0
        return None
    if cls == _last:
        _streak += 1
    else:
        _last, _streak = cls, 1
    if _streak >= cfg.DIGIT_STABLE_N:
        return (cls, conf)
    return None


def _infer(img, cfg):
    # TODO: 现场接 K230 KPU 数字模型；此处占位返回 None
    return (None, 0)
