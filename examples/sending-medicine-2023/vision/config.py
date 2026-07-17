# ★ 现场标定集中处 —— 阈值/ROI/曝光/串口（光照变了就改这里）
UART_ID = 1
BAUD = 115200                 # 与 contracts/protocol 一致

# 巡线（GRAYSCALE）
GRAY_THRESHOLD = (0, 60)      # 黑线灰度区间，现场标
ROI = (0, 200, 320, 40)       # x,y,w,h：取画面下部一条带，现场标

# 色块（RGB）
BLOB_THRESH = [(30, 100, 15, 127, 15, 127)]   # LAB，现场标

# 数字识别采信
DIGIT_STABLE_N = 3            # 连续 N 帧一致才采信（防误识）

# 模式
MODE_LINE, MODE_BLOB, MODE_DIGIT = 0, 1, 2
