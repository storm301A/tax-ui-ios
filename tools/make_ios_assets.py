"""生成 iOS 需要的 AppIcon（1024）与 LaunchScreen 启动图。

设计稿来源：web/icons/icon-512.png（蓝底 + 白色盾牌 + 「税」字），
这里只取其中的盾牌 + 税字（白色部分）作为蒙版，重新铺一层干净的蓝色渐变，
避免把 512 直接放大到 1024 之后发糊，也去掉图标底部那行小字（60pt 下不可读）。
"""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "icons" / "icon-512.png"
ICON_DIR = ROOT / "ios" / "App" / "App" / "Assets.xcassets" / "AppIcon.appiconset"
SPLASH_DIR = ROOT / "ios" / "App" / "App" / "Assets.xcassets" / "Splash.imageset"

TOP = np.array([52, 172, 255], dtype=np.float64)
BOTTOM = np.array([10, 114, 250], dtype=np.float64)


def gradient(w: int, h: int) -> Image.Image:
    ramp = np.linspace(0, 1, h)[:, None, None]
    arr = TOP * (1 - ramp) + BOTTOM * ramp
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def mark() -> Image.Image:
    """从 512 图标里取出「盾牌 + 税」的白色蒙版（RGBA，白字透明底）。"""
    src = np.array(Image.open(SRC).convert("RGB")).astype(np.float64)
    # 只取上半部分，底部那行「国家税务总局发布」不要
    crop = src[16:352, 20:492]
    mn = crop.min(axis=2)
    alpha = np.clip((mn - 140) / 95.0, 0, 1)
    rgba = np.zeros((crop.shape[0], crop.shape[1], 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def build_icon() -> None:
    size = 1024
    canvas = gradient(size, size)
    m = mark()
    # 盾牌在图标中占宽约 78%，垂直居中略偏上
    target_w = int(size * 0.78)
    target_h = round(m.height * target_w / m.width)
    m = m.resize((target_w, target_h), Image.LANCZOS)
    x = (size - target_w) // 2
    y = (size - target_h) // 2 - int(size * 0.015)
    canvas.paste(m, (x, y), m)
    canvas.save(ICON_DIR / "AppIcon-512@2x.png", optimize=True)
    print("icon", canvas.size)


def build_splash() -> None:
    size = 2732
    canvas = gradient(size, size)
    m = mark()
    target_w = int(size * 0.24)
    target_h = round(m.height * target_w / m.width)
    m = m.resize((target_w, target_h), Image.LANCZOS)
    canvas.paste(m, ((size - target_w) // 2, (size - target_h) // 2), m)
    for name in ("splash-2732x2732.png", "splash-2732x2732-1.png", "splash-2732x2732-2.png"):
        canvas.save(SPLASH_DIR / name, optimize=True)
    print("splash", canvas.size)


if __name__ == "__main__":
    build_icon()
    build_splash()
