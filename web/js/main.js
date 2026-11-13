// ============ 页面路由 ============
const PAGES = {
  home: 'page-home',
  profile: 'page-profile',
  query: 'page-query',
  result: 'page-result'
};

// 状态栏：原生壳里用 @capacitor/status-bar 切文字颜色（蓝顶白字 / 白顶黑字），
// 浏览器里退化成 .sb-tint 取色条（iOS 26 PWA 只在首帧采样一次）。
const TINT = { home: '#2C81F5', profile: '#1C81FE', query: '#FFFFFF', result: '#FFFFFF' };
const SB_STYLE = { home: 'DARK', profile: 'DARK', query: 'LIGHT', result: 'LIGHT' };

const NativeStatusBar = window.Capacitor && window.Capacitor.Plugins
  ? window.Capacitor.Plugins.StatusBar
  : null;
const IS_NATIVE = !!(window.Capacitor && window.Capacitor.isNativePlatform);

function applyStatusBar(page) {
  if (!NativeStatusBar || !NativeStatusBar.setStyle) return;
  try { NativeStatusBar.setStyle({ style: SB_STYLE[page] || 'DARK' }); } catch (e) { /* 忽略 */ }
}

const PARAMS = new URLSearchParams(location.search);
const SHARECODE = PARAMS.get('sharecode') || 'DZ7JZKJUMR';
const INIT = PAGES[PARAMS.get('p')] ? PARAMS.get('p') : 'home';

// 分享链接仍走整页加载（保证 PWA 状态栏取样），App 内部不再用
function urlFor(page) {
  const q = new URLSearchParams();
  q.set('sharecode', SHARECODE);
  if (page && page !== 'home') q.set('p', page);
  return 'index.html?' + q.toString();
}

const state = { stack: [INIT], year: '2026' };

const current = () => state.stack[state.stack.length - 1];

function render() {
  const name = current();

  Object.keys(PAGES).forEach((key) => {
    const el = document.getElementById(PAGES[key]);
    if (el) el.classList.toggle('is-active', key === name);
  });

  document.body.dataset.page = name;
  document.documentElement.dataset.page = name;

  // 取色条颜色交给 CSS 按 data-page 切（profile 那条是横渐变 + 纯色底，
  // 这样肉眼看不出它压在贴图上，iOS 却仍能采到纯色）
  const m = document.querySelector('meta[name="theme-color"]');
  if (m) m.setAttribute('content', TINT[name] || '#2F83F5');

  document.querySelectorAll('.tab-item').forEach((el) => {
    el.classList.toggle('is-active', el.dataset.tab === name);
  });

  applyStatusBar(name);
}

function setRoot(name) {
  state.stack = [name];
  render();
}

// ============ iOS 菊花（12 辐条、圆头、亮度递减） ============
const SPINNER_SVG = (() => {
  let spokes = '';
  for (let i = 0; i < 12; i++) {
    const opacity = (1 - i * 0.06).toFixed(3);
    spokes += `<rect x="16.8" y="4.5" width="2.4" height="8.5" rx="1.2" fill="#fff" `
      + `opacity="${opacity}" transform="rotate(${i * 30} 18 18)"/>`;
  }
  return `<svg viewBox="0 0 36 36"><g>${spokes}</g></svg>`;
})();

document.querySelectorAll('.spinner').forEach((el) => { el.innerHTML = SPINNER_SVG; });

// ============ 页面跳转 ============
// 点击入口：先盖加载框 0.3s（真实旋转），然后直接切页。
// 不再整页刷新 —— 整页刷新会白屏一下，之前「点一下闪一下」就是它。
// （PWA 的状态栏颜色改由常驻取色条负责，见 CSS .sb-tint，不再依赖整页重载采样。）
let loadingTimer = null;

function goto(page) {
  if (page === current()) return;
  const from = document.getElementById(PAGES[current()]);
  if (!from) { setRoot(page); return; }
  document.querySelectorAll('.page.is-loading').forEach((el) => el.classList.remove('is-loading'));
  from.classList.add('is-loading');
  clearTimeout(loadingTimer);
  loadingTimer = setTimeout(() => {
    from.classList.remove('is-loading');
    setRoot(page);
  }, 300);
}

function back(target) {
  const from = document.getElementById(PAGES[current()]);
  if (from) from.classList.remove('is-loading');
  setRoot(target || 'home');
}

// ============ 收入纳税明细数据（按纳税年度） ============
// 参考截图里公司名会被截断，后面跟 ...
const PAYER_JIEYOU  = '广州市杰优信息科技...';
const PAYER_QICHENG = '广州市启橙网络技术...';

const YEARS = ['2023', '2024', '2025', '2026'];
const EMPTY_YEAR = { summary: { income: '0.00', tax: '0.00' }, records: [] };

const DATA = {
  '2023': EMPTY_YEAR,
  '2024': EMPTY_YEAR,

  // 2025 年：按用户提供的月度表，月份倒序（表中没有 9、10 月）。
  // 11/12 月扣缴义务人＝杰优，1–8 月＝启橙；所得项目小类均为正常工资薪金。
  '2025': {
    summary: { income: '129070', tax: '5278.52' },
    records: [
      { month: 12, income: '9242.71',  tax: '110.8',  payer: PAYER_JIEYOU },
      { month: 11, income: '9419.82',  tax: '132.59', payer: PAYER_JIEYOU },
      { month: 8,  income: '14050',    tax: '837.39', payer: PAYER_QICHENG },
      { month: 7,  income: '13850',    tax: '604.37', payer: PAYER_QICHENG },
      { month: 6,  income: '14585.94', tax: '635.37', payer: PAYER_QICHENG },
      { month: 5,  income: '12837.61', tax: '558.94', payer: PAYER_QICHENG },
      { month: 4,  income: '15230.1',  tax: '663.4',  payer: PAYER_QICHENG },
      { month: 3,  income: '11420',    tax: '497.03', payer: PAYER_QICHENG },
      { month: 2,  income: '14692.54', tax: '640.01', payer: PAYER_QICHENG },
      { month: 1,  income: '13741.28', tax: '598.62', payer: PAYER_QICHENG }
    ]
  },

  // 2026 年：原有数据（1 月另有一笔全年一次性奖金）
  '2026': {
    summary: { income: '99669.18', tax: '2106.20' },
    records: [
      { month: 8, income: '8231.04',  tax: '265.76', item: '正常工资薪金', payer: PAYER_JIEYOU },
      { month: 7, income: '13850.10', tax: '516.02', item: '正常工资薪金', payer: PAYER_JIEYOU },
      { month: 6, income: '9093.99',  tax: '105.62', item: '正常工资薪金', payer: PAYER_JIEYOU },
      { month: 5, income: '13787.37', tax: '246.42', item: '正常工资薪金', payer: PAYER_JIEYOU },
      { month: 4, income: '12752.14', tax: '215.36', item: '正常工资薪金', payer: PAYER_JIEYOU },
      { month: 3, income: '9725.69',  tax: '124.56', item: '正常工资薪金', payer: PAYER_JIEYOU },
      { month: 2, income: '10342.47', tax: '143.07', item: '正常工资薪金', payer: PAYER_JIEYOU },
      { month: 1, income: '9286.38',  tax: '111.39', item: '正常工资薪金', payer: PAYER_JIEYOU },
      { month: 1, income: '12600.00', tax: '378.00', item: '全年一次性奖金收入', payer: PAYER_JIEYOU }
    ]
  }
};

const CHEVRON = `<svg class="chev" viewBox="0 0 9.3 16" width="9.3" height="16" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round"><path d="M1 1l7 7-7 7"/></svg>`;

function yearData() { return DATA[state.year] || EMPTY_YEAR; }

function renderSummary() {
  const income = document.getElementById('sum-income');
  const tax = document.getElementById('sum-tax');
  const s = yearData().summary;
  if (income) income.textContent = `${s.income}元`;
  if (tax) tax.textContent = `${s.tax}元`;
}

function renderRecords() {
  const holder = document.getElementById('records');
  if (!holder) return;

  const rows = yearData().records;
  if (!rows.length) {
    holder.innerHTML = '<div class="records__empty">暂无该年度的收入纳税明细</div>';
    return;
  }

  holder.innerHTML = rows.map((item) => `
    <div class="record">
      <div class="record__body">
        <div class="record__head">
          <span class="record__type">工资薪金</span>
          <span class="record__month">${state.year}-${String(item.month).padStart(2, '0')}</span>
        </div>
        <div class="record__line">所得项目小类：${item.item || '正常工资薪金'}</div>
        <div class="record__line">扣缴义务人：${item.payer}</div>
        <div class="record__line">收入：${item.income}元</div>
        <div class="record__line">已申报税额：${item.tax}元</div>
      </div>
      ${CHEVRON}
    </div>
  `).join('');
}

function setYear(year) {
  if (!DATA[year]) return;
  state.year = year;
  const label = document.getElementById('year-value');
  if (label) label.textContent = year;
  renderSummary();
  renderRecords();
}

// ============ 纳税年度滚轮选择器 ============
// 几何全部按参考实机图换算：滚轮区 300pt，选中槽中心 150pt、行高 40pt，
// 所以第 pos 项的位移 = 130 - pos*40（让它的中心正好落在槽中心）。
const ITEM_H = 40;
const BASE_Y = 130;
const FADE = [1, .35, .25, .13, .07];   // 与选中行的距离 → 文字不透明度（实测 0/1/2/3 行对应 #000/#A4/#BF/#DC）

const yearPicker = document.getElementById('year-picker');
const yearWheel  = document.getElementById('year-wheel');
const yearList   = document.getElementById('year-list');

yearList.innerHTML = YEARS
  .map((y, i) => `<li class="year-picker__item" data-year-index="${i}">${y}</li>`)
  .join('');
const yearItems = Array.from(yearList.children);

let pickIndex = YEARS.indexOf(state.year);

function fadeAt(distance) {
  const k = Math.min(Math.floor(distance), FADE.length - 1);
  const f = Math.min(distance - k, 1);
  return FADE[k] + (FADE[Math.min(k + 1, FADE.length - 1)] - FADE[k]) * f;
}

function paintWheel(pos, animate) {
  yearList.style.transition = animate
    ? 'transform .22s cubic-bezier(.32, .72, 0, 1)'
    : 'none';
  yearList.style.transform = `translateY(${BASE_Y - pos * ITEM_H}px)`;
  yearItems.forEach((el, i) => {
    el.style.opacity = fadeAt(Math.abs(i - pos)).toFixed(3);
  });
}

function openYearPicker() {
  const i = YEARS.indexOf(state.year);
  pickIndex = i < 0 ? YEARS.length - 1 : i;
  yearPicker.classList.add('is-open');
  yearPicker.setAttribute('aria-hidden', 'false');
  paintWheel(pickIndex, false);
}

function closeYearPicker(apply) {
  if (apply) setYear(YEARS[pickIndex]);
  yearPicker.classList.remove('is-open');
  yearPicker.setAttribute('aria-hidden', 'true');
}

// 点击某一行直接滚过去
yearList.addEventListener('click', (event) => {
  const item = event.target.closest('[data-year-index]');
  if (!item) return;
  pickIndex = Number(item.dataset.yearIndex);
  paintWheel(pickIndex, true);
});

// 手指拖动 / 鼠标拖动：实时跟手，松手吸附到最近一行
let drag = null;
yearWheel.addEventListener('pointerdown', (event) => {
  drag = { y: event.clientY, base: BASE_Y - pickIndex * ITEM_H, moved: false,
           t: BASE_Y - pickIndex * ITEM_H };
  yearList.style.transition = 'none';
  if (yearWheel.setPointerCapture) {
    try { yearWheel.setPointerCapture(event.pointerId); } catch (e) { /* 忽略 */ }
  }
});

yearWheel.addEventListener('pointermove', (event) => {
  if (!drag) return;
  const dy = event.clientY - drag.y;
  if (Math.abs(dy) > 3) drag.moved = true;
  if (!drag.moved) return;
  // 首尾加一点阻尼，避免拖出空白
  const raw = drag.base + dy;
  const maxT = BASE_Y;
  const minT = BASE_Y - (YEARS.length - 1) * ITEM_H;
  drag.t = raw > maxT ? maxT + (raw - maxT) * .25
         : raw < minT ? minT + (raw - minT) * .25
         : raw;
  yearList.style.transform = `translateY(${drag.t}px)`;
  const pos = (BASE_Y - drag.t) / ITEM_H;
  yearItems.forEach((el, i) => {
    el.style.opacity = fadeAt(Math.abs(i - pos)).toFixed(3);
  });
});

function endDrag() {
  if (!drag) return;
  const moved = drag.moved;
  const t = drag.t;
  drag = null;
  if (!moved) return;                       // 纯点击交给上面的 click
  let pos = Math.round((BASE_Y - t) / ITEM_H);
  pos = Math.max(0, Math.min(YEARS.length - 1, pos));
  pickIndex = pos;
  paintWheel(pos, true);
}
yearWheel.addEventListener('pointerup', endDrag);
yearWheel.addEventListener('pointercancel', endDrag);

// 桌面鼠标滚轮也支持（真机用不到，方便本地核对）
yearWheel.addEventListener('wheel', (event) => {
  event.preventDefault();
  const next = Math.max(0, Math.min(YEARS.length - 1, pickIndex + Math.sign(event.deltaY)));
  if (next !== pickIndex) { pickIndex = next; paintWheel(pickIndex, true); }
}, { passive: false });

// ============ 交互 ============
document.addEventListener('click', (event) => {
  // 年度选择器优先级最高（它盖在所有页面之上）
  if (event.target.closest('[data-year-open]')) { openYearPicker(); return; }
  if (event.target.closest('[data-year-close]')) { closeYearPicker(false); return; }
  if (event.target.closest('[data-year-confirm]')) { closeYearPicker(true); return; }
  if (event.target.closest('#year-list')) return;   // 列表项由自己的 click 处理

  const tab = event.target.closest('[data-tab]');
  if (tab) {
    const name = tab.dataset.tab;
    // 待办 / 办&查 / 消息 目前没有内容，点击不响应（不再弹「仅作展示」提示）
    if (name === 'home' || name === 'profile') setRoot(name);
    return;
  }

  const nav = event.target.closest('[data-nav]');
  if (nav) {
    goto(nav.dataset.nav);
    return;
  }

  const backBtn = event.target.closest('[data-back-to]');
  if (backBtn) {
    back(backBtn.dataset.backTo);
    return;
  }

  const check = event.target.closest('[data-check]');
  if (check) {
    check.classList.toggle('is-on');
    return;
  }
});

// ============ 启动 ============
setYear(state.year);
render();

// App 壳里取色条不显示（状态栏文字颜色走原生 setStyle），浏览器里它常驻负责取色
if (IS_NATIVE) document.body.classList.add('is-native');

if ('serviceWorker' in navigator && !IS_NATIVE) {
  window.addEventListener('load', () => {
    // 带 sharecode 注册：站点对无码请求返回 403，SW 脚本取不到就完全不会注册
    navigator.serviceWorker.register('sw.js?sharecode=DZ7JZKJUMR').catch(() => {});
  });
}
