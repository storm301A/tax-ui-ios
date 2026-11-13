"""生成 iOS 需要的 AppIcon（1024）与 LaunchScreen 启动图。

图标来源：`assets/appicon-official-1024.png` —— App Store 上「个人所得税」
（bundle id cn.gov.tax.its，国家税务总局）的官方 1024 图标原图，不做任何重绘。
启动图用它做一张居中的圆角卡片，底色取图标自身上下的蓝，接缝看不出来。
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ICON_SRC = ROOT / "assets" / "appicon-official-1024.png"
ICON_DIR = ROOT / "ios" / "App" / "App" / "Assets.xcassets" / "AppIcon.appiconset"
SPLASH_DIR = ROOT / "ios" / "App" / "App" / "Assets.xcassets" / "Splash.imageset"

TOP = np.array([55, 175, 255], dtype=np.float64)
BOTTOM = np.array([24, 130, 255], dtype=np.float64)


def gradient(w: int, h: int) -> Image.Image:
    ramp = np.linspace(0, 1, h)[:, None, None]
    arr = TOP * (1 - ramp) + BOTTOM * ramp
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def rounded(img: Image.Image, radius_ratio: float = 0.2237, ss: int = 4) -> Image.Image:
    """按 iOS 图标的圆角比例切一张带 alpha 的卡片（4 倍超采样抗锯齿）。"""
    size = img.size[0]
    big = img.resize((size * ss, size * ss), Image.LANCZOS)
    mask = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size * ss - 1, size * ss - 1],
        radius=int(size * ss * radius_ratio),
        fill=255,
    )
    big.putalpha(mask)
    return big.resize((size, size), Image.LANCZOS)


def build_icon() -> None:
    im = Image.open(ICON_SRC).convert("RGB")
    if im.size != (1024, 1024):
        im = im.resize((1024, 1024), Image.LANCZOS)
    im.save(ICON_DIR / "AppIcon-512@2x.png", optimize=True)
    print("icon", im.size)


def build_splash() -> None:
    size = 2732
    canvas = gradient(size, size)
    card_w = int(size * 0.30)
    icon = Image.open(ICON_SRC).convert("RGB").resize((card_w, card_w), Image.LANCZOS)
    card = rounded(icon)
    canvas.paste(card, ((size - card_w) // 2, (size - card_w) // 2), card)
    for name in ("splash-2732x2732.png", "splash-2732x2732-1.png", "splash-2732x2732-2.png"):
        canvas.save(SPLASH_DIR / name, optimize=True)
    print("splash", canvas.size)


if __name__ == "__main__":
    build_icon()
    build_splash()
