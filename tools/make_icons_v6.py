# -*- coding: utf-8 -*-
"""从设计稿高清原图（1344x1792，棋盘格透明）重新抠出首页四个入口图标。

设计稿的图标不是规整圆角方块：彩色方块后面叠了一张浅色「纸片」，外面还有很淡的投影。
所以不能用饱和色块的 bbox 直接截（会切掉衬底），也不能把棋盘格涂白（会露白方块）。
做法：
  1. 色度 max-min 判前景（棋盘格是中性灰，色度≈0；图标任何部分都有色偏）；
  2. 闭运算补缝 -> 填洞（方块内的白色图形被色块包住，必须补回）；
  3. 只用最大连通域，边缘 1.2px 羽化；
  4. 预乘 alpha 后 Lanczos 缩放，避免半透明边缘发白/发暗。

对齐锚点用「高饱和色块本体」（色度>120，浅色衬底色度只有 60~90，会被排除），
这样新旧版本都能量到同一个东西，屏幕上位置与尺寸才不会漂。
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = {
    "annual": r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-13T03-14-34-032Z-832e57f5.jpg",
    "detail": r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-13T03-14-34-033Z-4024ded1.jpg",
    "record": r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-13T03-14-34-031Z-3bb22ac2.jpg",
    "more":   r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-13T03-14-34-030Z-7f7e4b54.jpg",
}
ORDER = ["annual", "detail", "record", "more"]   # svc1..svc4
OLD_CSS = {1: (39.6, 7.9, -34.5), 2: (37.2, 9.2, -33.5),
           3: (36.5, 9.0, -33.9), 4: (37.1, 8.7, -33.6)}
OLD_DIR = ".tmp/v2/img_backup"
OUT_DIR = "web/img"
DPR = 3 * 1.35          # 输出 4.05 倍于屏幕尺寸


def block_bbox(rgb, alpha, thr=120):
    """色块本体（高饱和）的 bbox: (x0, y0, w, h)"""
    s = rgb.max(axis=2) - rgb.min(axis=2)
    m = (s > thr) & (alpha > 200)
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = lab == (int(np.argmax(sizes)) + 1)
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1


def extract(path, sat_thr=24):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    h, w, _ = a.shape
    s = a.max(axis=2) - a.min(axis=2)

    m = s > sat_thr
    m[600:, :] = False                       # 下方是大标题文字，排除
    m = ndi.binary_closing(m, np.ones((7, 7)))
    m = ndi.binary_fill_holes(m)
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = lab == (int(np.argmax(sizes)) + 1)

    alpha = ndi.gaussian_filter(m.astype(np.float32), 1.2)
    alpha = np.clip((alpha - 0.35) / 0.5, 0, 1)

    ys, xs = np.where(alpha > 0.02)
    pad = 2
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
    x1, y1 = min(w - 1, xs.max() + pad), min(h - 1, ys.max() + pad)

    rgb = np.clip(a[y0:y1 + 1, x0:x1 + 1], 0, 255).astype(np.uint8)
    al = (alpha[y0:y1 + 1, x0:x1 + 1] * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, al]), "RGBA"), (x0, y0)


def premul_resize(im, size):
    a = np.asarray(im, dtype=np.float32)
    al = a[:, :, 3:4] / 255.0
    pre = np.dstack([a[:, :, :3] * al, a[:, :, 3:4]])
    out = np.asarray(Image.fromarray(np.clip(pre, 0, 255).astype(np.uint8), "RGBA")
                     .resize(size, Image.LANCZOS), dtype=np.float32)
    oa = out[:, :, 3:4]
    orgb = np.where(oa > 0, out[:, :, :3] / np.maximum(oa / 255.0, 1e-6), 0)
    return Image.fromarray(np.dstack([np.clip(orgb, 0, 255), oa]).astype(np.uint8), "RGBA")


def main():
    # ---- 旧版：色块在屏幕上的位置/尺寸（作为不变量）----
    old = {}
    for i in range(1, 5):
        im = Image.open(os.path.join(OLD_DIR, "icon-svc%d.png" % i)).convert("RGBA")
        a = np.asarray(im)
        bx, by, bw, bh = block_bbox(a[:, :, :3].astype(np.int16), a[:, :, 3])
        css_w, css_l, css_t = OLD_CSS[i]
        k = css_w / im.width
        old[i] = dict(w=bw * k, left=css_l + bx * k, top=css_t + by * k)
        print("old svc%d 色块 %.2f x %.2f pt  @ (%.2f, %.2f)" % (i, bw * k, bh * k,
                                                                old[i]["left"], old[i]["top"]))

    rows = []
    for i, key in enumerate(ORDER, start=1):
        im, (ox, oy) = extract(SRC[key])
        a = np.asarray(im)
        bx, by, bw, bh = block_bbox(a[:, :, :3].astype(np.int16), a[:, :, 3])
        k = old[i]["w"] / bw                      # pt per px
        size = (max(1, round(im.width * k * DPR)), max(1, round(im.height * k * DPR)))
        out = premul_resize(im, size)
        out.save(os.path.join(OUT_DIR, "icon-svc%d.png" % i), optimize=True)

        css_w = out.width / DPR
        css_h = out.height / DPR
        css_l = old[i]["left"] - bx * k
        css_t = old[i]["top"] - by * k
        rows.append((i, key, out.width, out.height, css_w, css_h, css_l, css_t,
                     os.path.getsize(os.path.join(OUT_DIR, "icon-svc%d.png" % i)) / 1024))

    print("\n#  name    px       css w x h          left x top           KB")
    for r in rows:
        print("%d  %-7s %4dx%-4d %7.2f x %-8.2f %7.2f x %-8.2f %.1f" %
              (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]))
    print("\n最负 top = %.2f  ->  .services 的 padding-top 必须大于 %.1f" %
          (min(r[7] for r in rows), -min(r[7] for r in rows)))


if __name__ == "__main__":
    main()
