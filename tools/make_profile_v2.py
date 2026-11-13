# -*- coding: utf-8 -*-
"""我的页贴图处理：
1) 抹掉状态栏的时间/信号/电量：横向中值定位字形 -> 行内按已知像素线性插值回填
   （插值只依赖邻域，不会像多项式外推那样在右端高光区留下色块），由 iOS 原生状态栏覆盖
2) 「退出登录」以下整段填成 #F5F6FA（底部导航改用真实 HTML 胶囊）
"""
import numpy as np
from PIL import Image, ImageFilter

SRC = r'C:/Users/star/.workbuddy/clipboard-images/clipboard-2026-11-12T13-15-03-631Z-8a0bc7ea.jpg'
DST = r'E:/workbuddy存储/2026-11-12-16-43-27/web/img/profile-page.jpg'

im = Image.open(SRC).convert('RGB')
a = np.asarray(im).astype(np.float64)
H, W, _ = a.shape

# ---------- 1) 状态栏图标回填 ----------
BAND = 106                                  # 只处理 0..105（头像圆环从 118 起）
top = a[:BAND]

bg = np.zeros_like(top)
for c in range(3):
    ch = Image.fromarray(top[:, :, c].astype(np.uint8))
    bg[:, :, c] = np.asarray(ch.filter(ImageFilter.MedianFilter(51))).astype(np.float64)
mask = np.abs(top - bg).max(axis=2) > 7
mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8))
                  .filter(ImageFilter.MaxFilter(11))) > 0
mask[:, :3] = False
mask[:, -3:] = False
print('masked px', mask.sum())

xs = np.arange(W)
out = a.copy()
for y in range(BAND):
    known = ~mask[y]
    if mask[y].sum() == 0 or known.sum() < 60:
        continue
    xk = xs[known]
    for c in range(3):
        out[y, mask[y], c] = np.interp(xs[mask[y]], xk, out[y, known, c])

band = Image.fromarray(np.clip(out[:BAND], 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
out[:BAND] = np.asarray(band).astype(np.float64)

# ---------- 2) 底部填充 ----------
BOT = 1596
fill = np.median(out[1620:1700, 20:860].reshape(-1, 3), axis=0)
FEATHER = 14
for i in range(H - BOT):
    y = BOT + i
    w = min(1.0, i / FEATHER)
    out[y] = out[y] * (1 - w) + fill * w

out = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(out).save(DST, quality=92, subsampling=1)
print('saved', W, H, 'fill', fill.astype(int))

# ---------- 3) 顶部接缝融合（见 tools/blend_profile_top.py） ----------
exec(open(r'E:/workbuddy存储/2026-11-12-16-43-27/tools/blend_profile_top.py',
          encoding='utf-8').read())
