# -*- coding: utf-8 -*-
"""「我的」页整屏贴图 v5（iPhone 15 Pro 3x = 1179x2556）。

来源：用户给的干净整屏设计稿 885x1920（无状态栏文字、无假底栏），
宽高比 885/1920 = 0.4609，iPhone 15 Pro 1179/2556 = 0.4613，等比放大即可铺满。

文字清晰度：源图是 JPG，直接 1.33x 放大后笔画发虚。
  1) 中段 y=140..1600 与上一张同内容、不同压缩的截图做 50% 叠加 —— 两次 JPG
     噪声互不相关，叠加后噪点明显下降（顶/底不能叠：旧图那两段有状态栏文字和假底栏）。
  2) Lanczos 放大到 1179x2556。
  3) 「墨色加深」：只对近中性、偏暗的像素做 S 曲线压深，把抗锯齿灰边往黑推，
     笔画变实；蓝色渐变 / 橙色卡片 / 彩色图标饱和度高，自动被排除。
  4) 轻度 USM（r=0.9 / 95%）提笔画边缘，不产生白光晕。

用法：python tools/make_profile_v4.py
"""
import os
import numpy as np
from PIL import Image, ImageFilter

NEW = r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-13T04-31-30-040Z-1f581672.jpg"
OLD = r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-13T03-14-34-028Z-9260706a.jpg"
OUT = "web/img/profile-page.png"
SIZE = (1179, 2556)          # iPhone 15 Pro @3x
BLEND_TOP, BLEND_BOT = 140, 1600
FEATHER = 12

new = np.asarray(Image.open(NEW).convert("RGB"), dtype=np.float64)
old = np.asarray(Image.open(OLD).convert("RGB"), dtype=np.float64)
assert new.shape == (1920, 885, 3), new.shape
assert old.shape == new.shape, old.shape

# ---- 1) 中段双图叠加降噪，两端羽化 ----
w = np.zeros((new.shape[0], 1, 1), dtype=np.float64)
w[BLEND_TOP:BLEND_BOT] = 1.0
for i in range(FEATHER):
    t = (i + 1) / FEATHER
    w[BLEND_TOP - FEATHER + i] = t
    w[BLEND_BOT + i] = 1.0 - t
src = new * (1 - 0.5 * w) + old * (0.5 * w)

# ---- 2) 等比放大 ----
out = Image.fromarray(np.clip(src, 0, 255).astype(np.uint8), "RGB")
out = out.resize(SIZE, Image.LANCZOS)

# ---- 3) 墨色加深（只作用于黑字 / 深灰线条） ----
a = np.asarray(out, dtype=np.float64)
L = a.mean(axis=2)
sat = a.max(axis=2) - a.min(axis=2)
m = np.clip((225 - L) / 190, 0, 1) * np.clip((70 - sat) / 50, 0, 1)
a = np.clip(a - (4 * 22 * m * (1 - m))[:, :, None], 0, 255)
out = Image.fromarray(a.astype(np.uint8), "RGB")

# ---- 4) 轻度锐化 ----
out = out.filter(ImageFilter.UnsharpMask(radius=0.9, percent=95, threshold=3))
out.save(OUT, optimize=True)
print(OUT, out.size, "%.0f KB" % (os.path.getsize(OUT) / 1024))
