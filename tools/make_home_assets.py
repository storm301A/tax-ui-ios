# -*- coding: utf-8 -*-
"""首页素材：两张卡片整块贴图 + 四个服务入口图标 + 通知条铃铛。"""
import numpy as np
from PIL import Image, ImageDraw

SHOT = r'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T13-15-03-630Z-073ff695.jpg'
SVC = r'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T13-15-03-633Z-39e396b0.png'
MORE = r'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T13-15-03-634Z-144c18b7.png'
BELL = r'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T13-15-03-633Z-211f7276.png'
OUT = r'E:/workbuddy存储/2026-11-12-16-43-27/web/img/'


def round_mask(size, radius, ss=4):
    w, h = size
    m = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=radius * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def slice_card(src, box, radius, out_name):
    im = Image.open(src).convert('RGB').crop(box).convert('RGBA')
    im.putalpha(round_mask(im.size, radius))
    im.save(OUT + out_name)
    print(out_name, im.size)


# 卡片 1：2025 综合所得年度汇算（另做一个 2 倍超采样版本供高清屏用）
slice_card(SHOT, (27, 382, 857, 842), 30, 'hero-card.png')
# 卡片 2：重点服务推荐 · 专项附加扣除
slice_card(SHOT, (27, 1030, 857, 1401), 30, 'special-card.png')


def icon(src, box, radius, out_name, scale=1.0):
    im = Image.open(src).convert('RGB').crop(box).convert('RGBA')
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    im.putalpha(round_mask(im.size, radius))
    im.save(OUT + out_name)
    print(out_name, im.size)


# 图标方块：源图 3.623 px/pt，显示 31.5 × 27 pt
K = 1.312  # 第四张导出图偏小，放大到同一比例
icon(SVC, (69, 42, 183, 140), 26, 'icon-svc1.png')
icon(SVC, (477, 39, 591, 137), 26, 'icon-svc2.png')
icon(SVC, (891, 39, 1005, 140), 26, 'icon-svc3.png')
icon(MORE, (55, 50, 142, 126), 26 * K, 'icon-svc4.png', scale=K)

# 铃铛：按蓝通道估 alpha 并反预乘，叠在米色底上无白边
b = Image.open(BELL).convert('RGB')
ba = np.asarray(b).astype(float)
cream = np.array([251.0, 242.0, 227.0])
alpha = np.clip((cream[2] - ba[:, :, 2]) / (cream[2] - 60.0), 0, 1)
color = (ba - cream * (1 - alpha)[:, :, None]) / np.maximum(alpha, 1e-3)[:, :, None]
color = np.clip(color, 0, 255)
ys, xs = np.where(alpha > 0.04)
box = (xs.min() - 1, ys.min() - 1, xs.max() + 2, ys.max() + 2)
rgba = np.dstack([color, alpha * 255])[box[1]:box[3], box[0]:box[2]]
img = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA')
img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
img.save(OUT + 'bell.png')
print('bell.png', img.size, box)
