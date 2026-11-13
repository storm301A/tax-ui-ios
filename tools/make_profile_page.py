# -*- coding: utf-8 -*-
"""把「我的」页面截图做成整页贴图：抹掉顶部状态栏的时间/信号/电量等信息。

做法：先检测出状态栏上的亮色图标/文字，再用拉普拉斯扩散（邻域平均迭代）
把这些像素按周围渐变平滑补齐，避免留下涂抹痕迹。
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

WEB = Path(__file__).resolve().parent.parent / "web"
IMG = WEB / "img"
SRC = Path(r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T10-39-04-396Z-ddb54f0f.jpg")

BAND = 124  # 状态栏高度（像素）

im = Image.open(SRC).convert("RGB")
W, H = im.size
arr = np.asarray(im).astype(np.float64)

top = im.crop((0, 0, W, BAND))
a = np.asarray(top).astype(np.int16)

# 1) 只在状态栏图标可能出现的两个横向区间内检测，避免误伤背景高光
med = np.asarray(top.filter(ImageFilter.MedianFilter(size=61))).astype(np.int16)
cand = np.abs(a - med).max(2) > 5

zone = np.zeros_like(cand)
zone[0:118, 40:310] = True     # 左侧：时间 + 静音图标
zone[0:118, 555:880] = True    # 右侧：信号 / Wi-Fi / 电量
mask = cand & zone

# 3) 膨胀，覆盖抗锯齿边缘
m = mask.astype(np.uint8)
for _ in range(7):
    m = np.maximum.reduce([np.roll(m, 1, 1), m, np.roll(m, -1, 1),
                           np.roll(m, 1, 0), m, np.roll(m, -1, 0)])
mask = m.astype(bool)
mask[-6:, :] = False   # 保留底边作为扩散边界
print("masked px:", int(mask.sum()), "of", int(mask.size))

# 4) 逐行多项式拟合背景：用该行未被遮挡的像素拟合平滑曲线，再求遮挡处的值
work = arr[:BAND].copy()
xs_all = np.arange(W, dtype=np.float64)
for y in range(BAND):
    row = work[y]
    known = ~mask[y]
    if known.sum() < 40 or mask[y].sum() == 0:
        continue
    for c in range(3):
        coef = np.polyfit(xs_all[known], row[known, c], 6)
        pred = np.polyval(coef, xs_all[mask[y]])
        row[mask[y], c] = pred
    work[y] = row
print("poly fill done")

out = arr.copy()
out[:BAND] = work

res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

# 5) 与主体做 6px 羽化过渡，消除接缝
blended = Image.new("RGB", (W, H))
blended.paste(res, (0, 0))
body = im.crop((0, BAND - 6, W, H))
blended.paste(body, (0, BAND - 6))

IMG.mkdir(exist_ok=True)
dst = IMG / "profile-page.jpg"
blended.save(dst, quality=90, optimize=True, progressive=True)
print("saved", dst, dst.stat().st_size // 1024, "KB")

prev = WEB.parent / ".preview"
blended.crop((0, 0, W, 240)).save(prev / "z_prof_clean.png")
blended.crop((560, 0, 885, 130)).resize((650, 260), Image.LANCZOS).save(prev / "z_prof_tr.png")
