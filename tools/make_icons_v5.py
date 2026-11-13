# -*- coding: utf-8 -*-
"""直接使用设计稿里的图标（含后置浅色形状 + 柔和投影），只把棋盘格背景做成透明。

关键点：
- 图标是「不规则形状」：彩色方块 + 后面一层浅色圆角方片（向上/左侧露出）+ 一圈很淡的投影。
  按方块 bbox 裁会切掉浅色形状，硬阈值切 alpha 会切掉投影，看起来就有「被剪断」的边。
- 棋盘格是中性灰（245 / 255），浅色形状带明显色偏（如 220,201,246），用
  「饱和度 > 10 或最暗通道 < 238」能把两者分开；投影则用亮度做渐变 alpha 保留。
"""
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = {
    1: 'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T16-21-02-804Z-4024ded1.jpg',
    2: 'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T16-21-02-805Z-7f7e4b54.jpg',
    3: 'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T16-21-02-807Z-3bb22ac2.jpg',
    4: 'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T16-21-02-808Z-832e57f5.jpg',
}

OUT = 'web/img'
TARGET_BLOCK_H = 28.8      # pt，色块视觉高度
TARGET_BLOCK_LEFT = 10.9   # pt，色块左边缘（相对卡片）
TARGET_BLOCK_TOP = -29.0   # pt，色块上边缘（卡片上沿之上）
BLOCK_PX_H = 240           # 输出 PNG 里色块的高度（像素，显示尺寸 33pt ≈ 99px@3x，2.4x 足够）
PAD = 14                   # 裁切外扩（保留投影）


def shape_mask(a):
    sat = a.max(2) - a.min(2)
    mn = a.min(2)
    m = (sat > 10) | (mn < 238)
    h, w = m.shape
    m[int(h * 0.5):, :] = False
    m[:, int(w * 0.6):] = False
    m = ndimage.binary_closing(m, np.ones((7, 7)))
    m = ndimage.binary_fill_holes(m)
    lab, n = ndimage.label(m)
    if n > 1:
        sz = ndimage.sum(m, lab, range(1, n + 1))
        m = lab == (int(np.argmax(sz)) + 1)
    return m, sat


def main():
    rows = []
    for key, path in SRC.items():
        im = Image.open(path).convert('RGB')
        a = np.array(im).astype(np.int16)
        m, sat = shape_mask(a)

        ys, xs = np.where(m)
        x0, x1 = max(xs.min() - PAD, 0), min(xs.max() + PAD + 1, im.width)
        y0, y1 = max(ys.min() - PAD, 0), min(ys.max() + PAD + 1, im.height)

        mask = m[y0:y1, x0:x1]
        rgb = a[y0:y1, x0:x1].astype(np.float32)
        mn = rgb.min(2)

        # 主体 alpha：1px 羽化，边缘抗锯齿
        solid = np.clip((ndimage.gaussian_filter(mask.astype(np.float32), 0.8) - 0.45) / 0.32, 0, 1)

        # 外围投影：亮度做 alpha，只在主体外 12px 的环带里生效
        band = ndimage.binary_dilation(mask, np.ones((3, 3)), iterations=12) & ~mask
        shadow = np.clip((253.0 - mn) / 16.0, 0, 1) * band
        shadow = ndimage.gaussian_filter(shadow, 1.0)

        alpha = np.clip(np.maximum(solid, shadow * 0.85), 0, 1)
        alpha[alpha < 0.04] = 0

        # 边缘反预乘，去掉白边（只在主体范围做）
        af = np.clip(alpha, 1e-3, 1)[..., None]
        color = (rgb - 255.0 * (1 - af)) / af
        color = np.where(alpha[..., None] > 0.35, color, rgb)
        color = np.clip(color, 0, 255)
        color[alpha == 0] = 0

        b = (sat[y0:y1, x0:x1] > 90) & mask
        bys, bxs = np.where(b)
        bh = bys.max() - bys.min() + 1

        k = BLOCK_PX_H / bh
        out = Image.fromarray(np.dstack([color, alpha * 255]).astype(np.uint8), 'RGBA')
        out = out.resize((max(1, round(out.width * k)), max(1, round(out.height * k))), Image.LANCZOS)
        out.save(f'{OUT}/icon-svc{key}.png', optimize=True)

        s = TARGET_BLOCK_H / BLOCK_PX_H
        css_h = round(TARGET_BLOCK_H * out.height / BLOCK_PX_H, 1)
        css_w = round(TARGET_BLOCK_H * out.width / BLOCK_PX_H, 1)
        top = round(TARGET_BLOCK_TOP - bys.min() * k * s, 1)
        left = round(TARGET_BLOCK_LEFT - bxs.min() * k * s, 1)
        rows.append((key, css_w, css_h, top, left))
        print(f'{key}: png{out.size} block {bh} -> CSS w{css_w} h{css_h} top{top} left{left}')

    with open('.tmp/icon_css.txt', 'w', encoding='utf-8') as f:
        for key, w, h, t, l in rows:
            f.write(f'.service:nth-of-type({key}) .service__icon '
                    f'{{ width: {w}px; height: {h}px; top: {t}px; left: {l}px; }}\n')


if __name__ == '__main__':
    main()
