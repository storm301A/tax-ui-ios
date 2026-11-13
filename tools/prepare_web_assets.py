"""生成 Web 版所需的图片素材（从手机截图裁切）。

运行：python tools/prepare_web_assets.py
输出：web/img/banner.png、web/img/bell.png、web/img/tab-*.png
"""

from pathlib import Path

from PIL import Image, ImageFilter

WEB = Path(__file__).resolve().parent.parent
IMG = WEB / "img"

# 截图来源
SHOT_SCROLL = Path(r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T09-48-27-699Z-570f8114.jpg")
SHEET_HOME = Path(r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T09-48-27-705Z-afbca3d8.png")
SHEET_PROF = Path(r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T09-48-27-706Z-60166244.png")


def upscale_sharpen(im: Image.Image, size, radius=1.5, percent=58) -> Image.Image:
    return im.resize(size, Image.LANCZOS).filter(
        ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=2)
    )


def transparent(im: Image.Image, bg=None, cutoff=0.03) -> Image.Image:
    """把浅色底去掉，转成带 alpha 的图（颜色按 alpha 反预乘，贴回原底色可完全还原）。"""
    im = im.convert("RGB")
    w, h = im.size
    if bg is None:
        corners = [im.getpixel((0, 0)), im.getpixel((w - 1, 0)), im.getpixel((0, h - 1)), im.getpixel((w - 1, h - 1))]
        bg = tuple(sorted(c[i] for c in corners)[len(corners) // 2] for i in range(3))

    out = Image.new("RGBA", (w, h))
    src, dst = im.load(), out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            a = max((bg[i] - c) / bg[i] for i, c in enumerate((r, g, b)))
            a = max(0.0, min(1.0, a))
            if a < cutoff:
                dst[x, y] = (0, 0, 0, 0)
                continue
            rgb = [max(0, min(255, round((c - (1 - a) * bg[i]) / a))) for i, c in enumerate((r, g, b))]
            dst[x, y] = (rgb[0], rgb[1], rgb[2], round(a * 255))
    return out


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)

    # ---------- 1. 经营所得申报 banner（12..381pt × 96pt，按 3x 输出）----------
    shot = Image.open(SHOT_SCROLL).convert("RGB")
    banner = shot.crop((27, 755, 858, 971))
    banner = upscale_sharpen(banner, (1107, 288))
    banner.save(IMG / "banner.png", optimize=True)
    print("banner.png", banner.size)

    # ---------- 2. 通知条铃铛（约 22×18pt）----------
    bell_src = Image.open(r"C:\Users\star\.workbuddy\clipboard-images\clipboard-2026-11-12T09-48-27-701Z-bcc7772f.jpg").convert("RGB")
    bell = bell_src.crop((42, 290, 94, 334))
    bell = upscale_sharpen(bell, (66, 55), radius=1.2, percent=45)
    transparent(bell, bg=(253, 242, 226)).save(IMG / "bell.png", optimize=True)
    print("bell.png", bell.size)

    # ---------- 3. 底部导航图标 ----------
    home = Image.open(SHEET_HOME).convert("RGB")
    prof = Image.open(SHEET_PROF).convert("RGB")

    # (源图, 左, 上, 右, 下)  —— 均按各自图标的墨迹包围盒
    jobs = {
        "tab-home-on": (home, 37, 46, 118, 128),
        "tab-home-off": (prof, 54, 55, 139, 137),
        "tab-todo": (home, 288, 46, 370, 128),
        "tab-work": (home, 539, 46, 621, 128),
        "tab-msg": (home, 792, 46, 875, 128),
        "tab-profile-on": (prof, 1061, 55, 1146, 137),
        "tab-profile-off": (home, 1043, 46, 1126, 128),
    }
    for name, (src, x0, y0, x1, y1) in jobs.items():
        icon = src.crop((x0, y0, x1, y1))
        icon = transparent(icon)
        icon.save(IMG / f"{name}.png", optimize=True)
        print(f"{name}.png", icon.size)


if __name__ == "__main__":
    main()
