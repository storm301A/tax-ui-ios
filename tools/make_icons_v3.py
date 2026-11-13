# -*- coding: utf-8 -*-
"""从设计稿（棋盘格底的 1344x1792 JPG）里把四个服务图标**原样**抠出来。

与 v2 的差别：
  * v2 用「饱和连通域」直接取 bbox，取到的框紧贴图形外沿，四边都被切平了
    （量出来左右边缘各有 130+ 行 alpha>10，等于圆角被裁掉）。
  * v3 先定位主干，再外扩一圈安全边距，然后在该窗口内用「从边界泛洪近白像素」
    得到外部区域，内部一律不透明 —— 图形（含后置浅色衬底、内部白色图形）完整保留，
    只是把棋盘格背景去掉。
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
CB = Path('C:/Users/star/.workbuddy/clipboard-images')
OUT = ROOT / 'web' / 'img'

SRC = {
    '1': 'clipboard-2026-11-12T15-21-50-018Z-832e57f5.jpg',   # 综合所得年度汇算
    '2': 'clipboard-2026-11-12T15-21-50-012Z-4024ded1.jpg',   # 收入纳税明细
    '3': 'clipboard-2026-11-12T15-21-50-015Z-7f7e4b54.jpg',   # 纳税记录开具
    '4': 'clipboard-2026-11-12T15-21-50-016Z-3bb22ac2.jpg',   # 更多功能
}

H_OUT = 240          # 输出高（源图约 310px，缩到 240 保留细节）


def outside_mask(rgb, thr=238):
    """从窗口四边泛洪，标记「外面的近白背景」（棋盘格 246/255 都算背景）。"""
    near_white = rgb.min(axis=2) >= thr
    h, w = near_white.shape
    lab, n = ndimage.label(near_white)
    border_ids = set(lab[0, :].tolist()) | set(lab[-1, :].tolist()) \
        | set(lab[:, 0].tolist()) | set(lab[:, -1].tolist())
    border_ids.discard(0)
    return np.isin(lab, list(border_ids))


def cut(path):
    img = Image.open(path).convert('RGB')
    a = np.array(img).astype(np.int16)
    h, w = a.shape[:2]
    sat = a.max(2) - a.min(2)

    # 1) 只在左上象限找主干，避开底部彩色胶囊
    probe = sat > 90
    probe[int(h * .45):, :] = False
    probe[:, int(w * .55):] = False
    ys, xs = np.where(probe)
    cx0, cx1, cy0, cy1 = xs.min(), xs.max(), ys.min(), ys.max()

    # 2) 外扩安全边距（主干 bbox 不含后置衬底与圆角外沿）；
    #    衬底是往左上偏移的，所以外扩后还要检查图形有没有顶到窗口边，顶到就继续扩。
    step = max(cx1 - cx0, cy1 - cy0) * .085
    for i in range(4):
        pad = int(step * (1 + i * .6))
        x0, x1 = max(cx0 - pad, 0), min(cx1 + pad + 1, w)
        y0, y1 = max(cy0 - pad, 0), min(cy1 + pad + 1, h)
        win = a[y0:y1, x0:x1]
        outside = outside_mask(win.astype(np.int16))
        inside = ~outside
        touch = (inside[0, 1:-1].any() or inside[-1, 1:-1].any()
                 or inside[1:-1, 0].any() or inside[1:-1, -1].any())
        if not touch or (x0 == 0 and y0 == 0 and x1 == w and y1 == h):
            break

    # 去掉零星噪点（JPEG 边缘的浅色小点）
    lab, n = ndimage.label(inside)
    if n > 1:
        sizes = ndimage.sum(inside, lab, range(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:][sizes > 400] = True
        inside = keep[lab]

    # 3) 软边 + 反预乘去白边
    m = ndimage.gaussian_filter(inside.astype(np.float32), 0.9)
    alpha = np.clip((m - .25) / .55, 0, 1)
    alpha[alpha < .02] = 0

    c = win.astype(np.float32)
    fg = (c - 255.0 * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3)
    fg = np.clip(fg, 0, 255)

    rgba = np.dstack([fg, alpha * 255]).astype(np.uint8)
    im = Image.fromarray(rgba, 'RGBA')

    # 4) 按 alpha 收边，但四边各留 2px 透明，保证圆角不被切
    bb = im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    im = im.crop((max(bb[0] - 2, 0), max(bb[1] - 2, 0),
                  min(bb[2] + 2, im.size[0]), min(bb[3] + 2, im.size[1])))

    hh = H_OUT
    ww = round(im.size[0] * hh / im.size[1])
    return im.resize((ww, hh), Image.LANCZOS)


def main():
    for k, f in SRC.items():
        im = cut(CB / f)
        dst = OUT / f'icon-svc{k}.png'
        im.save(dst)
        al = np.array(im)[:, :, 3]
        print(f'svc{k}', im.size,
              'edges L/R/T/B =',
              int((al[:, 0] > 10).sum()), int((al[:, -1] > 10).sum()),
              int((al[0, :] > 10).sum()), int((al[-1, :] > 10).sum()),
              dst.stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
