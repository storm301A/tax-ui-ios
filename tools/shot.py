# -*- coding: utf-8 -*-
"""生成仅用于本地校验的抓屏页 _shot.html（从 index.html 派生，注入安全区与固定宽度）。

用法：python tools/shot.py
"""
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
src = (WEB / "index.html").read_text(encoding="utf-8")

inject = """
<style>
  /* App（Capacitor）几何：webview 铺满整屏 393x852（含状态栏那一段），
     env(safe-area-inset-top)=59 由 CSS 变量直接给死。 */
  :root { --safe-top: 59px !important; --safe-bottom: 34px !important; }
  html, body { width: 393px !important; height: 852px !important; overflow: hidden !important; }
  .page { inset: 0 !important; width: 393px !important; height: 852px !important; }
  .tabbar { position: absolute !important; left: 10px !important; right: auto !important; top: 766.3px !important; bottom: auto !important; width: 373px !important; }
  /* fixed 弹层在桌面 520x1000 视口里会铺满整个视口，抓屏时钉回 393x852 的机身 */
  .year-picker { position: absolute !important; left: 0 !important; right: auto !important; top: 0 !important; bottom: auto !important; width: 393px !important; height: 852px !important; }
  *, *::before, *::after { animation-duration: 0s !important; transition-duration: 0s !important; }
  .spinner { animation: none !important; }

  .sb-tint { display: none !important; }   /* 截图里不需要，真机上由 CSS/原生控制 */

</style>
<script>
  // 记录元素几何，便于 ?rects=1 时 dump
  window.addEventListener('load', () => {
    const q = new URLSearchParams(location.search);
    if (q.get('p')) { state.stack = [q.get('p')]; render(); }
    if (q.get('year')) { setYear(q.get('year')); }
    if (q.get('yp')) { openYearPicker(); }
    if (q.get('loading')) {
      const el = document.getElementById(PAGES[q.get('p')] || 'page-query');
      if (el) el.classList.add('is-loading');
      clearTimeout(loadingTimer);
    }
    if (q.get('selftest')) {
      const log = [];
      const yv = () => document.getElementById('year-value').textContent;
      log.push('init=' + yv());
      openYearPicker();
      log.push('open=' + document.getElementById('year-picker').classList.contains('is-open'));
      document.querySelector('[data-year-index="2"]').click();
      document.querySelector('[data-year-confirm]').click();
      log.push('picked=' + yv());
      log.push('income=' + document.getElementById('sum-income').textContent);
      log.push('tax=' + document.getElementById('sum-tax').textContent);
      log.push('rows=' + document.querySelectorAll('#records .record').length);
      log.push('firstPayer=' + document.querySelector('#records .record__line:nth-of-type(2)').textContent);
      log.push('closed=' + !document.getElementById('year-picker').classList.contains('is-open'));
      const pre = document.createElement('pre');
      pre.id = 'selftest-result';
      pre.textContent = 'SELFTEST ' + log.join(' | ');
      document.body.appendChild(pre);
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
