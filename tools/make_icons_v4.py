# -*- coding: utf-8 -*-
"""直接使用用户给的四张设计稿：裁出图标区域，棋盘格背景抹成白色，不做任何重绘/改色。

之前几版都是「重新抠图 + 重建形状」，出来和设计稿对不上。
这一版只做三件事：
  1) 用饱和度定位图标（含它背后那块浅色衬底）的整体外接框；
  2) 向外留一点白边后裁切（像素原封不动）；
  3) 从裁切框四边泛洪，把「浅灰棋盘格 / 纯白卡片」统一抹成纯白，
     这样贴到白色卡片上时看不到任何棋盘格。

同时输出每个图标「彩色块」在裁切图内的相对位置，供 CSS 计算 top/left/宽高。
"""
import json
import pathlib

import numpy as np
from PIL import Image
from scipy import ndimage

SRC = {
    'svc1': 'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T15-57-43-294Z-832e57f5.jpg',  # 综合所得年度汇算
    'svc2': 'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T15-57-43-295Z-4024ded1.jpg',  # 收入纳税明细
    'svc3': 'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T15-57-43-296Z-3bb22ac2.jpg',  # 纳税记录开具
    'svc4': 'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T15-57-43-297Z-7f7e4b54.jpg',  # 更多功能
}
OUT = pathlib.Path('web/img')


def icon_bbox(a):
    """整块图标（彩色主体 + 背后浅色衬底）的外接框。"""
    sat = a.max(2) - a.min(2)
    h, w = sat.shape
    m = sat > 14                      # 卡片白底 sat~0，棋盘格 sat~0-3，衬底 sat 20+
    m[int(h * 0.42):, :] = False      # 只看上半部分，避开底部彩色胶囊
    m[:, int(w * 0.62):] = False
    m = ndimage.binary_closing(m, np.ones((5, 5)))
    lab, n = ndimage.label(m)
    if n == 0:
        raise RuntimeError('no icon found')
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = lab == (int(np.argmax(sizes)) + 1)
    ys, xs = np.where(keep)
    return xs.min(), xs.max(), ys.min(), ys.max()


def block_bbox(crop):
    """裁切图里「强彩色主体」（不考虑浅色衬底）的外接框，用于确定显示尺寸。"""
    sat = crop.max(2) - crop.min(2)
    m = sat > 80
    m = ndimage.binary_closing(m, np.ones((5, 5)))
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = lab == (int(np.argmax(sizes)) + 1)
    ys, xs = np.where(keep)
    return xs.min(), xs.max(), ys.min(), ys.max()


def whitened_bg(crop):
    """返回「与裁切框四边连通的近白 / 棋盘格背景」的掩码。"""
    sat = crop.max(2) - crop.min(2)
    bright = (sat < 20) & (crop.min(2) > 226)
    lab, n = ndimage.label(bright)
    edge = np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])
    edge = set(int(v) for v in np.unique(edge) if v)
    if not edge:
        return np.zeros(crop.shape[:2], bool)
    return np.isin(lab, list(edge))


meta = {}
for key, path in SRC.items():
    im = Image.open(path).convert('RGB')
    a = np.array(im)
    x0, x1, y0, y1 = icon_bbox(a.astype(np.int16))
    pad = int(round(max(x1 - x0, y1 - y0) * 0.10))
    cx0, cx1 = max(x0 - pad, 0), min(x1 + pad + 1, im.width)
    cy0, cy1 = max(y0 - pad, 0), min(y1 + pad + 1, im.height)
    crop = a[cy0:cy1, cx0:cx1].astype(np.int16).copy()
    bg = whitened_bg(crop)
    rgba = np.dstack([crop.astype(np.uint8), np.where(bg, 0, 255).astype(np.uint8)])
    bx0, bx1, by0, by1 = block_bbox(crop)
    out = Image.fromarray(rgba)
    out.save(OUT / f'icon-{key}.png', optimize=True)
    meta[key] = dict(
        w=out.width, h=out.height,
        blockW=int(bx1 - bx0 + 1), blockH=int(by1 - by0 + 1),
        blockCX=float((bx0 + bx1 + 1) / 2), blockCY=float((by0 + by1 + 1) / 2),
    )
    print(key, out.size, 'block', bx1 - bx0 + 1, 'x', by1 - by0 + 1,
          'cx', meta[key]['blockCX'], 'cy', meta[key]['blockCY'])

print(json.dumps(meta, indent=1))
