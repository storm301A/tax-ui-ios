# -*- coding: utf-8 -*-
"""生成「我的」页贴图：只提升清晰度，顶部不再烘焙纯色。

顶部与系统状态栏（纯色）的衔接改由 CSS 渐变遮罩 .profile-fade 完成，
好处是过渡带可以压到最上面（状态栏下沿 ~58px），不会盖到头像，
而且渐变是连续函数，不会出现「一条边」。

源图 .tmp/profile-before-blend.jpg 已经抹掉状态栏的时间/信号/电量。
原图 885x1920（2.25x），这里放大到 1179x2556（3x）做 1:1 设备像素输出。
"""
import numpy as np
from PIL import Image, ImageFilter

BASE = r'E:/workbuddy存储/2026-11-12-16-43-27/'
SRC = BASE + '.tmp/profile-before-blend.jpg'
DST = BASE + 'web/img/profile-page.jpg'

OUT_W, OUT_H = 1179, 2556

im = Image.open(SRC).convert('RGB')
print('src', im.size)

big = im.resize((OUT_W, OUT_H), Image.LANCZOS)
big = big.filter(ImageFilter.UnsharpMask(radius=1.3, percent=55, threshold=2))

a = np.asarray(big).astype(np.float64)
a[1:-1] = (a[:-2] + a[1:-1] * 2 + a[2:]) / 4.0          # 压掉块状噪点
big = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
big.save(DST, quality=90, subsampling=0, optimize=True)
print('saved', big.size)

arr = np.asarray(big).astype(int)
# 顶部一行各处的颜色（决定状态栏取色条该用哪个值）
print('top row', [list(arr[0, x]) for x in (4, 300, 589, 880, 1174)])
print('row5 avg', arr[5, 40:1140].mean(axis=0).round())
