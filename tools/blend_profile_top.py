# -*- coding: utf-8 -*-
"""「我的」页顶部过渡：让状态栏纯色与贴图渐变连续，但不碰头像。

约束：
  * iOS 独立模式的状态栏是**纯色**（#2F83F5，页面加载时采样 .sb-tint 得到），
    而贴图顶部是「左深右浅」的横向渐变，纯色无法同时对上两端。
  * 贴图里的头像白圈 64pt 就开始了（144px），几乎贴着状态栏下沿，
    所以任何「往下填纯色」的过渡都会把头像上沿糊掉。

做法：
  * 背景：0~59pt 填 #2F83F5（状态栏盖住，看不见），59~100pt 用 smoothstep 混回原图；
  * 头像：椭圆权重保护（中心 442/251，半径 125/122，羽化），整块像素原样保留。

输入固定取 .tmp/profile-before-blend.jpg（未处理的原始贴图），可重复执行。
"""
import numpy as np
from PIL import Image

SRC = r'E:/workbuddy存储/2026-11-12-16-43-27/web/img/profile-page.jpg'
SRC_BAK = r'E:/workbuddy存储/2026-11-12-16-43-27/.tmp/profile-before-blend.jpg'

S = 2.2519
BASE = np.array([47.0, 131.0, 245.0])      # #2F83F5
SEAM = int(round(59 * S))                   # 133px：状态栏下沿
FULL = int(round(100 * S))                  # 225px：过渡结束

CX, CY = 442.0, 251.0                       # 头像圆心
RX, RY = 125.0, 122.0                       # 含外圈光晕
FEATHER = 0.10                              # 羽化宽度（相对半径）

im = Image.open(SRC_BAK).convert('RGB')
a = np.asarray(im).astype(np.float64)
H, W, _ = a.shape

yy, xx = np.mgrid[0:H, 0:W]
d = np.sqrt(((xx - CX) / RX) ** 2 + ((yy - CY) / RY) ** 2)
protect = np.clip((1.0 - d) / FEATHER, 0.0, 1.0)   # 头像内 1，外面 0

out = a.copy()
for y in range(0, FULL):
    if y < SEAM:
        bg = 0.0
    else:
        u = (y - SEAM) / (FULL - SEAM)
        bg = u * u * (3 - 2 * u)                   # smoothstep
    p = np.maximum(bg, protect[y])                 # 保留原图的权重
    out[y] = a[y] * p[:, None] + BASE * (1 - p)[:, None]

out = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(out).save(SRC, quality=92, subsampling=1)
print('seam', SEAM, 'full', FULL, 'avatar cx/cy', CX, CY)
