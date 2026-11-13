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

const state = { stack: [INIT] };

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

// ============ 收入纳税明细数据 ============
const YEAR = '2026';

// 月份倒序：8月 → 1月；1月另有一笔全年一次性奖金
const RECORDS = [
  { month: 8, income: '8231.04', tax: '265.76', item: '正常工资薪金' },
  { month: 7, income: '13850.10', tax: '516.02', item: '正常工资薪金' },
  { month: 6, income: '9093.99', tax: '105.62', item: '正常工资薪金' },
  { month: 5, income: '13787.37', tax: '246.42', item: '正常工资薪金' },
  { month: 4, income: '12752.14', tax: '215.36', item: '正常工资薪金' },
  { month: 3, income: '9725.69', tax: '124.56', item: '正常工资薪金' },
  { month: 2, income: '10342.47', tax: '143.07', item: '正常工资薪金' },
  { month: 1, income: '9286.38', tax: '111.39', item: '正常工资薪金' },
  { month: 1, income: '12600.00', tax: '378.00', item: '全年一次性奖金收入' }
];

// 汇总（与上表合计一致）
const SUMMARY = { income: '99669.18', tax: '2106.20' };

// 参考截图里公司名会被截断，后面跟 ...
const PAYER = '广州市杰优信息科技...';

const CHEVRON = `<svg class="chev" viewBox="0 0 9.3 16" width="9.3" height="16" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round"><path d="M1 1l7 7-7 7"/></svg>`;

function renderSummary() {
  const income = document.getElementById('sum-income');
  const tax = document.getElementById('sum-tax');
  if (income) income.textContent = `${SUMMARY.income}元`;
  if (tax) tax.textContent = `${SUMMARY.tax}元`;
}

function renderRecords() {
  const holder = document.getElementById('records');
  if (!holder) return;

  holder.innerHTML = RECORDS.map((item) => `
    <div class="record">
      <div class="record__body">
        <div class="record__head">
          <span class="record__type">工资薪金</span>
          <span class="record__month">${YEAR}-${String(item.month).padStart(2, '0')}</span>
        </div>
        <div class="record__line">所得项目小类：${item.item}</div>
        <div class="record__line">扣缴义务人：${PAYER}</div>
        <div class="record__line">收入：${item.income}元</div>
        <div class="record__line">已申报税额：${item.tax}元</div>
      </div>
      ${CHEVRON}
    </div>
  `).join('');
}

// ============ 交互 ============
document.addEventListener('click', (event) => {
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
renderSummary();
renderRecords();
render();

// App 壳里取色条不显示（状态栏文字颜色走原生 setStyle），浏览器里它常驻负责取色
if (IS_NATIVE) document.body.classList.add('is-native');

if ('serviceWorker' in navigator && !IS_NATIVE) {
  window.addEventListener('load', () => {
    // 带 sharecode 注册：站点对无码请求返回 403，SW 脚本取不到就完全不会注册
    navigator.serviceWorker.register('sw.js?sharecode=DZ7JZKJUMR').catch(() => {});
  });
}
