# -*- coding: utf-8 -*-
"""从设计稿里抠「首页四个功能入口」的图标（色块 + 后方浅色衬底）。

设计稿背景是灰白棋盘格（原 PNG 的透明区被拍平），色块内部又有纯白图形，所以：
  * 先在左上象限用高饱和（sat > 80）定位色块本体，圈出一个局部窗口；
  * 窗口内用 sat > 20 取前景 —— 衬底是淡蓝/淡紫（sat 45~70），棋盘格 sat 0~3，能分开；
  * binary_fill_holes 把色块里的纯白图形补回来，取最大连通域；
  * 边缘 0.7px 高斯软化 + 反预乘去掉白边。
输出高 300px，页面显示 32pt（3x = 96px），余量充足。
"""
import numpy as np
from PIL import Image
from scipy import ndimage

BASE = r'E:/workbuddy存储/2026-11-12-16-43-27/'
SRCS = {
    'svc1': r'C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T14-42-42-542Z-832e57f5.jpg',  # 综合所得年度汇算
    'svc2': r'C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T14-42-42-543Z-4024ded1.jpg',  # 收入纳税明细
    'svc3': r'C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T14-42-42-541Z-3bb22ac2.jpg',  # 纳税记录开具
    'svc4': r'C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T14-42-42-540Z-7f7e4b54.jpg',  # 更多功能
}


def extract(path):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.float64)
    H, W, _ = a.shape
    sat = a.max(axis=2) - a.min(axis=2)

    # 1) 只在左上象限找色块，避免选中卡片底部的彩色胶囊按钮
    probe = sat > 80
    probe[int(H * 0.45):, :] = False
    probe[:, int(W * 0.55):] = False
    ys, xs = np.where(probe)
    bx0, bx1 = xs.min(), xs.max()
    by0, by1 = ys.min(), ys.max()

    # 2) 局部窗口里连衬底一起取
    pad_x0, pad_x1 = 90, 30
    pad_y0, pad_y1 = 90, 30
    wx0 = max(0, bx0 - pad_x0)
    wx1 = min(W, bx1 + pad_x1)
    wy0 = max(0, by0 - pad_y0)
    wy1 = min(H, by1 + pad_y1)

    win = sat[wy0:wy1, wx0:wx1]
    fg = win > 20
    fg = ndimage.binary_closing(fg, np.ones((5, 5)))
    fg = ndimage.binary_fill_holes(fg)
    lab, n = ndimage.label(fg)
    if n > 1:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        fg = lab == (np.argmax(sizes) + 1)
    print('  block', (bx0, by0, bx1, by1), 'window', (wx0, wy0, wx1, wy1))

    alpha = ndimage.gaussian_filter(fg.astype(np.float64), 0.7)
    alpha = np.clip((alpha - 0.15) / 0.70, 0, 1)

    white = np.array([255.0, 255.0, 255.0])
    color = (a[wy0:wy1, wx0:wx1] - white * (1 - alpha)[:, :, None]) \
        / np.maximum(alpha, 1e-3)[:, :, None]
    color = np.clip(color, 0, 255)

    ys2, xs2 = np.where(fg)
    cy0, cy1 = ys2.min(), ys2.max() + 1
    cx0, cx1 = xs2.min(), xs2.max() + 1
    rgba = np.dstack([color, alpha * 255])[cy0:cy1, cx0:cx1]
    out = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA')
    h = 240
    w = int(round(out.width * h / out.height))
    return out.resize((w, h), Image.LANCZOS)


for key, path in SRCS.items():
    print(key)
    icon = extract(path)
    dst = BASE + 'web/img/icon-%s.png' % key
    icon.save(dst, optimize=True)
    print('  ->', icon.size)

prev = Image.new('RGB', (4 * 320, 340), (232, 235, 242))
for i, key in enumerate(['svc1', 'svc2', 'svc3', 'svc4']):
    ic = Image.open(BASE + 'web/img/icon-%s.png' % key)
    ic = ic.resize((int(ic.width * 300 / ic.height), 300), Image.LANCZOS)
    prev.paste(ic, (10 + i * 320, 20), ic)
prev.save(BASE + '.tmp/icons_v2.png')
print('preview ok')
