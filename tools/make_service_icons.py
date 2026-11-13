# -*- coding: utf-8 -*-
"""从设计稿里扣出首页四个功能入口的图标（圆角方块 + 后方浅色衬底）。

设计稿背景是灰白棋盘格（模拟透明），方块内部有纯白图形，
所以不能用「与背景差异」直接算 alpha（会把白色图形也挖空），
做法是：先用饱和度找出彩色前景 -> 闭运算 + 填洞 -> 再软化边缘。
"""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

OUT = r'E:/workbuddy存储/2026-11-12-16-43-27/web/img'

SRC = {
    'svc1': ('C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T14-21-37-334Z-832e57f5.jpg', 'annual'),
    'svc2': ('C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T14-21-37-334Z-4024ded1.jpg', 'detail'),
    'svc3': ('C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T14-21-37-333Z-3bb22ac2.jpg', 'record'),
    'svc4': ('C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T14-21-37-331Z-7f7e4b54.jpg', 'more'),
}

for key, (path, label) in SRC.items():
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.float64)
    H, W, _ = a.shape

    sat = a.max(axis=2) - a.min(axis=2)
    mask = sat > 12

    # 只看左上角的图标区域，避免卡片文字、胶囊被误收
    keep = np.zeros_like(mask)
    keep[:620, :760] = True
    mask &= keep

    mask = ndimage.binary_closing(mask, structure=np.ones((5, 5)))
    mask = ndimage.binary_fill_holes(mask)

    lab, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        mask = lab == (int(np.argmax(sizes)) + 1)

    ys, xs = np.where(mask)
    x0, x1 = xs.min() - 2, xs.max() + 3
    y0, y1 = ys.min() - 2, ys.max() + 3

    # 边缘软化：先模糊再按原始像素重新确定阈值，避免出现硬边
    soft = np.asarray(
        Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    ).astype(np.float64) / 255.0

    rgba = np.dstack([a, soft * 255])[y0:y1, x0:x1]
    out = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA')
    out.save(f'{OUT}/icon-{key}.png', optimize=True)
    print(f'{key:5s} {label:8s} box=({x0},{y0})-({x1},{y1}) size={out.size}')
