# -*- coding: utf-8 -*-
"""生成 App 启动页图（0.5 秒）。

源图是 iPhone 15 Pro 整屏截图 1179x2556（正好 393x852pt @3x），带着：
  - 顶部状态栏：13:01 / 信号 / WiFi / 92% 电量 / 灵动岛浅点
  - 四周的圆角外框（深灰渐变）
  - 底部 home indicator 横条
这些都要抹掉；保留浅色水印方块、蓝色盾牌 logo、「个人所得税 / Individual
Income Tax」、底部「国家税务总局主办」与国徽。

产出：
  web/img/splash.png                     —— web 层 splash，1179x2556 全屏
  ios/.../Splash.imageset/*.png         —— 原生 LaunchScreen，2732x2732 正方形

原生 LaunchScreen.storyboard 用的是 scaleAspectFill + 2732 正方形资源。
在 1179x2556 屏幕上，aspectFill 会把正方形按高度缩放到 2556x2556，
再取中间 1179 宽 —— 对应源图 x=736..1996、y=0..2732。
所以把 splash 等比拉成 1260x2732 贴到 x=736，系统启动画面就与 web splash
逐像素对齐，两段拼接看不出跳变；两侧留白填纯白（本就是白底）。

用法：python tools/make_splash.py
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(r"E:\WeChat Files\xwechat_files\wxid_pfgfn5x1u5hp22_1085\temp\RWTemp\2026-11\ad0dc91c568e18341a77352959eb3a8d.png")
OUT_WEB = ROOT / "web" / "img" / "splash.png"
SPLASH_DIR = ROOT / "ios" / "App" / "App" / "Assets.xcassets" / "Splash.imageset"

W, H = 1179, 2556
WHITE = np.array([255, 255, 255], dtype=np.float64)


def feather(mask: np.ndarray, grow: int = 3, blur: float = 0.8) -> np.ndarray:
    """把二值掩膜膨胀 + 羽化，避免填补处出现硬边。"""
    from scipy import ndimage as ndi
    m = ndi.binary_dilation(mask, iterations=grow).astype(np.float64)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(blur)), dtype=np.float64) / 255.0
    return np.clip(m, 0, 1)[:, :, None]


def build_web_splash() -> Image.Image:
    a = np.asarray(Image.open(SRC).convert("RGB"), dtype=np.float64)
    assert a.shape[:2] == (H, W), a.shape

    dark = a.min(axis=2) < 238          # 深色字形/图标/外框/绿色电池
    # 灵动岛/摄像头是一小片很淡的蓝色反光 (241,249,255)，亮度高躲过了上面的判据；
    # 用 B-R 差值单独抓（浅灰水印方块 B-R≈0~1，不会被误伤）
    bluish = ((a[:, :, 2] - a[:, :, 0]) > 5) & (a.min(axis=2) > 220)
    mask = np.zeros((H, W), dtype=bool)

    # 1) 顶部状态栏整带（含时间、信号、WiFi、电量、灵动岛浅点、圆角外框）
    mask[:178, :] |= dark[:178, :]
    mask[:178, :] |= bluish[:178, :]

    # 2) 左右圆角外框：上/下段比中段宽，中段只剩最外 1~2px
    mask[:, :10] = True
    mask[:, W - 10:] = True
    mask[:230, :72] = True
    mask[:230, W - 72:] = True
    mask[2310:, :72] = True
    mask[2310:, W - 72:] = True

    # 3) 底部：home indicator 横条 + 底部圆角外框（「国家税务总局主办」在 2410~2460，保留）
    mask[2485:, :] = True

    alpha = feather(mask, grow=2, blur=0.7)
    out = a * (1 - alpha) + WHITE * alpha
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    im.save(OUT_WEB, optimize=True)
    print("web splash", im.size, "%.0f KB" % (OUT_WEB.stat().st_size / 1024))
    return im


def build_native_splash(web: Image.Image) -> None:
    S = 2732
    scale = S / H                      # 2556 -> 2732
    inner_w = round(W * scale)         # 1179 -> 1260
    x = (S - inner_w) // 2            # 736
    canvas = Image.new("RGB", (S, S), (255, 255, 255))
    canvas.paste(web.resize((inner_w, S), Image.LANCZOS), (x, 0))
    for name in ("splash-2732x2732.png", "splash-2732x2732-1.png", "splash-2732x2732-2.png"):
        canvas.save(SPLASH_DIR / name, optimize=True)
    print("native splash", canvas.size, "inner", inner_w, "x offset", x)


if __name__ == "__main__":
    w = build_web_splash()
    build_native_splash(w)
