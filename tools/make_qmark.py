# -*- coding: utf-8 -*-
"""把用户给的问号图片（白底、蓝色圆环 + 问号）切成透明 PNG。

源图是「纯白底 + 单一蓝色」的二值化插画，所以用红通道推 alpha 最干净：
    alpha = (255 - R) / (255 - R_fg)
再统一染成目标蓝，输出 64x64（页面上按 14.4pt 显示，约 4.4x 余量）。
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = Path('C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T15-21-50-021Z-12dffcd0.png')
DST = ROOT / 'web' / 'img' / 'icon-qmark.png'

FG = (66, 134, 244)      # 源图圆环的颜色
SIZE = 64


def main():
    a = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)

    # 取最暗像素当作前景色（稳健一点，避免 JPEG/缩放误差）
    dark = a.reshape(-1, 3)[a.reshape(-1, 3).sum(1).argmin()]
    r_fg = float(dark[0])
    alpha = np.clip((255.0 - a[:, :, 0]) / (255.0 - r_fg), 0, 1)
    alpha[alpha < .04] = 0

    rgba = np.zeros(a.shape[:2] + (4,), np.uint8)
    rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2] = FG
    rgba[:, :, 3] = (alpha * 255).round().astype(np.uint8)

    im = Image.fromarray(rgba, 'RGBA')
    bb = im.split()[3].getbbox()
    im = im.crop(bb)

    # 等比放到 SIZE，四周留 1px 透明
    inner = SIZE - 2
    im = im.resize((inner, inner), Image.LANCZOS)
    out = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(im, (1, 1))
    out.save(DST)
    print('saved', DST, out.size, DST.stat().st_size // 1024, 'KB', 'fg', dark)


if __name__ == '__main__':
    main()
