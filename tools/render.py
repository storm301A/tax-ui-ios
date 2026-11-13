# -*- coding: utf-8 -*-
"""本地抓屏：起静态服务 -> Edge headless 截图 -> 裁成 1179x2556（3x 的 393x852）。

用法：python tools/render.py home|profile|query|result [out.png]
"""
import subprocess
import sys
import time
import threading
import functools
import http.server
import socketserver
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'web'
EDGE = r'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
PORT = 8731


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(QuietHandler, directory=str(WEB))
    httpd = socketserver.TCPServer(('127.0.0.1', PORT), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else 'home'
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / '.tmp' / f'{page}.png'
    out = out if out.is_absolute() else ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)

    # 派生抓屏页
    subprocess.run([sys.executable, str(ROOT / 'tools' / 'shot.py')], check=True)

    httpd = serve()
    time.sleep(.4)
    raw = ROOT / '.tmp' / '_raw.png'
    raw.parent.mkdir(parents=True, exist_ok=True)
    if raw.exists():
        raw.unlink()

    extra = sys.argv[3] if len(sys.argv) > 3 else ''
    url = f'http://127.0.0.1:{PORT}/_shot.html?p={page}' + extra
    # 每次用全新目录，避免旧 profile 里缓存的 JS/CSS 影响校验（不删任何既有文件）
    profile = ROOT / '.tmp' / ('edgeprofile-%d' % time.time_ns())
    subprocess.run([
        EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars',
        f'--user-data-dir={profile}', '--force-device-scale-factor=3',
        '--window-size=520,1000', '--virtual-time-budget=2000',
        f'--screenshot={raw}', url
    ], check=False, timeout=90)

    img = Image.open(raw).convert('RGB')
    print('raw', img.size)
    img = img.crop((0, 0, 1179, 2556))
    img.save(out)
    print('saved', out, img.size)
    httpd.shutdown()


if __name__ == '__main__':
    main()
