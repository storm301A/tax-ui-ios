# -*- coding: utf-8 -*-
"""生成仅用于本地校验的抓屏页 _shot.html（从 index.html 派生，注入安全区与固定宽度）。

用法：python tools/shot.py
"""
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
src = (WEB / "index.html").read_text(encoding="utf-8")

inject = """
<style>
  /* 实机（独立模式）几何：视口 393x793，从屏幕 y=59 开始，页面内部 env(safe-area-inset-top)=0。
     所以这里把 .page 挪到 59，并让 safe-top 归零，页面里绝对定位的内容才和实机一致。 */
  :root { --safe-top: 0px !important; --safe-bottom: 34px !important; }
  html, body { width: 393px !important; height: 852px !important; overflow: hidden !important; }
  .page { inset: 59px auto auto 0 !important; width: 393px !important; height: 793px !important; }
  .tabbar { position: absolute !important; left: 10px !important; right: auto !important; top: 766.3px !important; bottom: auto !important; width: 373px !important; }
  *, *::before, *::after { animation-duration: 0s !important; }
  .spinner { animation: none !important; }

  /* 模拟 iOS 26 独立模式：webview 从状态栏下沿（59pt）开始，
     状态栏那一条由 iOS 用 html 的背景色绘制 —— 所以这里不用再画假的色条，
     只要把 .page 挪到 59，空出来的 59pt 自然露出 html 的背景色，与实机一致。 */
  .sb-tint { display: none !important; }

</style>
<script>
  // 记录元素几何，便于 ?rects=1 时 dump
  window.addEventListener('load', () => {
    const q = new URLSearchParams(location.search);
    if (q.get('p')) { state.stack = [q.get('p')]; render(); }
    if (q.get('loading')) {
      const el = document.getElementById(PAGES[q.get('p')] || 'page-query');
      if (el) el.classList.add('is-loading');
      clearTimeout(loadingTimer);
    }
    if (q.get('rects')) {
      const out = [];
      document.querySelectorAll('[class]').forEach((el, i) => {
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) return;
        out.push(el.className + '#' + i + ' x=' + r.x.toFixed(1) +
          ' y=' + r.y.toFixed(1) + ' w=' + r.width.toFixed(1) + ' h=' + r.height.toFixed(1));
      });
      const pre = document.createElement('pre');
      pre.id = 'rects';
      pre.style.cssText = 'position:absolute;z-index:999;left:0;top:0;font-size:6px;background:#fff';
      pre.textContent = out.join('\\n');
      document.body.appendChild(pre);
    }
  });
</script>
"""

src = src.replace("</head>", inject + "</head>")
(WEB / "_shot.html").write_text(src, encoding="utf-8")
print("wrote _shot.html")
