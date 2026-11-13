# -*- coding: utf-8 -*-
"""「我的」页整屏贴图 v4。

原图 885x1920（2.2519 px/pt，正好 393x852pt 比例），三处要处理：
  1) 顶部 0~132px 是真实状态栏（时间/信号/电量/静音图标），贴进页面会和系统状态栏重影
     -> 逐列求整段中位色作为背景，偏离 >22 的判为字形，再沿该列上下插值回填。
        不用「复制首行」补顶（头像光晕在 y≈110 就开始，复制会拉出一条竖向拖影）。
  2) 底部有一颗假底部导航（胶囊 + 红点 15），App 已有原生底栏 -> 1600 以下整段填背景色。
  3) 885px 放到 1179 物理像素会发糊 -> Lanczos 放大 + 轻 USM（半径 1.1 / 58%）。
"""
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

SRC = r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-13T03-14-34-028Z-9260706a.jpg"
SB_H = 132
CARD_END = 1600
BG = (243, 247, 250)

a = np.asarray(Image.open(SRC).convert("RGB"), dtype=np.float64)
H, W, _ = a.shape
assert (W, H) == (885, 1920), a.shape

# ---------- 1) 状态栏字形回填（拉普拉斯扩散修补） ----------
# 逐列插值会在亮光带里留下竖向条纹（信号/电量图标高、跨行多）。
# 改成热扩散：把掩膜像素初始化为该列中位色，反复用邻域均值扩散 400 次，
# 等价于解拉普拉斯方程 —— 对平滑渐变是最自然的补法，不会产生方向性条纹。
band = a[:SB_H]
bg_col = np.median(band, axis=0)
mask = np.abs(band - bg_col).max(axis=2) > 22
mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8))
                  .filter(ImageFilter.MaxFilter(13))) > 0
mask[:, :2] = False
mask[:, -2:] = False
print("遮罩像素", int(mask.sum()))

work = band.copy()
# 先按列竖向插值给个接近的初值（避免大块字形中心扩散不到位）
ys = np.arange(SB_H)
for x in range(W):
    m = mask[:, x]
    if not m.any():
        continue
    known = ~m
    if known.sum() < 30:
        work[:, x] = bg_col[x]
        continue
    for c in range(3):
        work[m, x, c] = np.interp(ys[m], ys[known], work[known, x, c])
# 再做 200 轮邻域扩散，把逐列插值的竖向条纹抹掉
for _ in range(200):
    sm = ndi.gaussian_filter1d(work, 1.6, axis=1)   # 只沿 x 扩散，别把 RGB 通道混掉
    work[mask] = sm[mask]
band = work
a[:SB_H] = np.asarray(Image.fromarray(np.clip(band, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(1.0))).astype(np.float64)

# ---------- 2) 抹掉假底栏 ----------
a[CARD_END:] = BG

# ---------- 3) 放大 + 锐化 ----------
out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
out = out.resize((1179, 2556), Image.LANCZOS)
out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=58, threshold=3))

out.save("web/img/profile-page.png", optimize=True)
out.save("web/img/profile-page.webp", quality=94, method=6)
for f in ("profile-page.png", "profile-page.webp"):
    print(f, out.size, "%.0f KB" % (os.path.getsize("web/img/" + f) / 1024))
