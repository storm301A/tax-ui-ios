// ============ 页面路由 ============
const PAGES = {
  home: 'page-home',
  profile: 'page-profile',
  query: 'page-query',
  result: 'page-result'
};

// iOS 只在**页面加载时**采样一次状态栏颜色，SPA 内切页不会重新采样。
// 所以「首页/我的」（顶部都是蓝色）留在单页内切换；
// 「收入纳税明细/结果」（顶部是白色导航栏）改成整页加载，让状态栏重新采样成白色。
const PARAMS = new URLSearchParams(location.search);
const SHARECODE = PARAMS.get('sharecode') || 'DZ7JZKJUMR';
const INIT = PAGES[PARAMS.get('p')] ? PARAMS.get('p') : 'home';

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
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  Object.keys(PAGES).forEach((key) => {
    const el = document.getElementById(PAGES[key]);
    if (!el) return;
    el.classList.toggle('is-active', key === name);
    if (key === name && !reduceMotion) {
      // 重新触发入场动画
      el.style.animation = 'none';
      void el.offsetWidth;
      el.style.animation = '';
    }
  });

  document.body.dataset.page = name;

  // 状态栏取色条：load 时被采样一次。首页与我的顶部都是 #2F83F5，
  // 子页面各自整页加载，靠这里给出的白色拿到白色状态栏。
  const TINT = { home: '#2F83F5', profile: '#2F83F5', query: '#FFFFFF', result: '#FFFFFF' };
  const tint = document.querySelector('.sb-tint');
  if (tint) tint.style.backgroundColor = TINT[name] || '#2F83F5';

  // 底部导航高亮跟随当前页
  document.querySelectorAll('.tab-item').forEach((el) => {
    el.classList.toggle('is-active', el.dataset.tab === name);
  });
}

function setRoot(name) {
  state.stack = [name];
  render();
}

let loadingTimer = null;

// 点击入口：先在当前页盖上加载框 0.2 秒，再整页跳转。
// （整页跳转是为了让 iOS 重新给状态栏采样成白色；加载框留在跳转前的页面上。）
function goto(page) {
  const from = document.getElementById(PAGES[current()]);
  if (!from) {
    location.href = urlFor(page);
    return;
  }
  document.querySelectorAll('.page.is-loading').forEach((el) => el.classList.remove('is-loading'));
  from.classList.add('is-loading');
  clearTimeout(loadingTimer);
  loadingTimer = setTimeout(() => {
    location.href = urlFor(page);
  }, 200);
}

function back(target) {
  location.replace(urlFor(target || 'home'));
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

// 从 bfcache 恢复时不会重新采样状态栏，重载一次保证颜色正确
window.addEventListener('pageshow', (event) => {
  if (event.persisted) location.reload();
});

// 状态栏取色条：iOS 采样完就没用了，留着会一直压住首页搜索框的上半截。
// 等 load（首帧 + 采样一定已经发生）后再淡出，慢网下最多等 1.2s 兜底。
(function dropTint() {
  let done = false;
  const hide = () => {
    if (done) return;
    done = true;
    setTimeout(() => document.body.classList.add('sb-done'), 260);
  };
  if (document.readyState === 'complete') hide();
  else window.addEventListener('load', hide);
  setTimeout(hide, 1200);
})();

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    // 带 sharecode 注册：站点对无码请求返回 403，SW 脚本取不到就完全不会注册
    navigator.serviceWorker.register('sw.js?sharecode=DZ7JZKJUMR').catch(() => {});
  });
}

