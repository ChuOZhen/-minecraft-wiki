// ============================================
// browser.js — 分层分类浏览（大类→小类→物品）
// ============================================

import {
  getCategories,
  getCategoryById,
  getSubcategories,
  getItemsBySubcategory,
  getItemsByCategory,
  getItemById,
  ensureData
} from './data.js';

const categoryGrid    = document.getElementById('category-grid');
const subcategoryTabs = document.getElementById('subcategory-tabs');
const itemGrid        = document.getElementById('item-grid');
const breadcrumb      = document.getElementById('breadcrumb');
const browserEmpty    = document.getElementById('browser-empty');
const browserRoot     = document.getElementById('browser-root');

let currentCategoryId    = null;
let currentSubcategoryId = null;

/**
 * 初始化浏览模块
 */
export function initBrowser() {
  window.addEventListener('hashchange', onHashChange);
  onHashChange(); // 首次加载
}

/**
 * 根据 URL hash 渲染对应视图
 */
function onHashChange() {
  const route = parseHash();

  ensureData().then(() => {
    if (route.itemId) {
      // 有物品详情 → 先恢复浏览背景再触发详情
      if (route.categoryId && route.subcategoryId) {
        renderItemGrid(route.categoryId, route.subcategoryId, /* updateHash */ false);
      } else if (route.categoryId) {
        renderSubcategoryTabs(route.categoryId, /* updateHash */ false);
      } else {
        renderCategoryGrid(/* updateHash */ false);
      }
      document.dispatchEvent(new CustomEvent('item-select', { detail: { id: route.itemId } }));
    } else if (route.categoryId && route.subcategoryId) {
      renderItemGrid(route.categoryId, route.subcategoryId, /* updateHash */ false);
    } else if (route.categoryId) {
      renderSubcategoryTabs(route.categoryId, /* updateHash */ false);
    } else {
      renderCategoryGrid(/* updateHash */ false);
    }
  });
}

/**
 * 解析 hash
 */
function parseHash() {
  const hash = window.location.hash.replace('#', '') || 'browser';
  const parts = hash.split('#');

  const result = { categoryId: null, subcategoryId: null, itemId: null };

  for (const part of parts) {
    if (part.startsWith('browser')) {
      const segments = part.split('/');
      result.categoryId    = segments[1] || null;
      result.subcategoryId = segments[2] || null;
    } else if (part.startsWith('item/')) {
      result.itemId = part.replace('item/', '');
    }
  }

  return result;
}

/**
 * 更新 hash（不触发 hashchange）
 */
function updateHash(categoryId, subcategoryId, itemId) {
  let hash = 'browser';
  if (categoryId) {
    hash += `/${categoryId}`;
    if (subcategoryId) hash += `/${subcategoryId}`;
  }
  if (itemId) hash += `#item/${itemId}`;

  const url = window.location.pathname + '#' + hash;
  history.replaceState(null, '', url);
}

// ============================================
// 第一层：大类卡片网格
// ============================================

function renderCategoryGrid(updateHashFlag = true) {
  currentCategoryId    = null;
  currentSubcategoryId = null;

  const categories = getCategories();
  categoryGrid.innerHTML = '';
  categoryGrid.classList.remove('hidden');
  subcategoryTabs.classList.add('hidden');
  itemGrid.classList.add('hidden');
  browserEmpty.classList.add('hidden');

  if (categories.length === 0) {
    browserEmpty.classList.remove('hidden');
    browserEmpty.querySelector('p').textContent = '暂无分类数据';
  }

  for (const cat of categories) {
    const card = buildCategoryCard(cat);
    categoryGrid.appendChild(card);
  }

  renderBreadcrumb(null, null);

  if (updateHashFlag) {
    history.pushState(null, '', window.location.pathname + '#browser');
  }
}

function buildCategoryCard(cat) {
  const card = document.createElement('div');
  card.className = 'category-card';

  // 优先使用 icon_item，否则回退第一个子类的第一个物品
  let iconUrl = '';
  if (cat.icon_item) {
    const iconItem = getItemById(cat.icon_item);
    if (iconItem) iconUrl = iconItem.icon_url;
  }
  if (!iconUrl) {
    const firstSub = cat.subcategories?.[0];
    if (firstSub && firstSub.items?.length > 0) {
      const firstItem = getItemById(firstSub.items[0]);
      if (firstItem) iconUrl = firstItem.icon_url;
    }
  }

  // 统计物品总数
  let count = 0;
  if (cat.subcategories) {
    for (const sub of cat.subcategories) {
      count += sub.items ? sub.items.length : 0;
    }
  }

  // FIX: DOM 版图标，不用 innerHTML 字符串拼接
  card.appendChild(createItemIcon(iconUrl, cat.name_zh, 48));
  const nameSpan = document.createElement('span');
  nameSpan.className = 'category-card-name';
  nameSpan.textContent = cat.name_zh;
  card.appendChild(nameSpan);
  const countSpan = document.createElement('span');
  countSpan.className = 'category-card-count';
  countSpan.textContent = count + ' 个物品';
  card.appendChild(countSpan);

  card.addEventListener('click', () => {
    renderSubcategoryTabs(cat.id);
  });

  return card;
}

// ============================================
// 第二层：小类标签页
// ============================================

function renderSubcategoryTabs(categoryId, updateHashFlag = true) {
  currentCategoryId    = categoryId;
  currentSubcategoryId = null;

  const cat = getCategoryById(categoryId);
  if (!cat) return;

  const subcats = getSubcategories(categoryId);

  // 有中类 → 自动选中第一个，直接渲染物品网格
  if (subcats.length > 0) {
    renderItemGrid(categoryId, subcats[0].id, updateHashFlag);
    return;
  }

  // 无中类 → 显示空状态
  categoryGrid.classList.add('hidden');
  subcategoryTabs.classList.remove('hidden');
  itemGrid.classList.add('hidden');
  browserEmpty.classList.add('hidden');

  subcategoryTabs.innerHTML = '';
  renderBreadcrumb(cat, null);

  if (updateHashFlag) {
    history.pushState(null, '', `#browser/${categoryId}`);
  }
}

// ============================================
// 第三层：物品网格
// ============================================

function renderItemGrid(categoryId, subcategoryId, updateHashFlag = true) {
  currentCategoryId    = categoryId;
  currentSubcategoryId = subcategoryId;

  const cat = getCategoryById(categoryId);
  const subcats = getSubcategories(categoryId);
  const currentSub = subcats.find(s => s.id === subcategoryId);

  categoryGrid.classList.add('hidden');
  subcategoryTabs.classList.remove('hidden');
  itemGrid.classList.remove('hidden');
  browserEmpty.classList.add('hidden');

  // 保留小类标签并高亮当前
  subcategoryTabs.innerHTML = '';
  for (const sub of subcats) {
    const tab = document.createElement('button');
    tab.className = 'subcategory-tab';
    if (sub.id === subcategoryId) tab.classList.add('active');
    tab.textContent = sub.name_zh;
    tab.addEventListener('click', () => {
      renderItemGrid(categoryId, sub.id);
    });
    subcategoryTabs.appendChild(tab);
  }

  // 渲染物品
  const items = getItemsBySubcategory(categoryId, subcategoryId);
  itemGrid.innerHTML = '';

  if (items.length === 0) {
    itemGrid.innerHTML = '<div class="browser-empty"><p>该小类暂无物品数据</p></div>';
  }

  for (const item of items) {
    const cell = buildItemCell(item);
    itemGrid.appendChild(cell);
  }

  renderBreadcrumb(cat, currentSub);

  if (updateHashFlag) {
    history.pushState(null, '', `#browser/${categoryId}/${subcategoryId}`);
  }
}

function buildItemCell(item) {
  const cell = document.createElement('div');
  cell.className = 'item-cell';
  cell.dataset.tooltip = item.name_en;
  // FIX: DOM 版图标，不用 innerHTML 字符串拼接
  cell.appendChild(createItemIcon(item.icon_url, item.name_zh, 32));
  const nameSpan = document.createElement('span');
  nameSpan.className = 'item-cell-name';
  nameSpan.textContent = item.name_zh;
  cell.appendChild(nameSpan);

  cell.addEventListener('click', () => {
    // 更新 URL hash（保留当前浏览位置 + 加入 item）
    updateHash(currentCategoryId, currentSubcategoryId, item.id);
    document.dispatchEvent(new CustomEvent('item-select', { detail: { id: item.id } }));
  });

  return cell;
}

// ============================================
// 面包屑导航
// ============================================

function renderBreadcrumb(cat, subcat) {
  breadcrumb.innerHTML = '';

  // "全部"
  const all = document.createElement('span');
  all.className = 'breadcrumb-item';
  if (cat) {
    all.dataset.route = 'browser';
    all.addEventListener('click', () => renderCategoryGrid());
  } else {
    all.classList.add('breadcrumb-active');
  }
  all.textContent = '全部';
  breadcrumb.appendChild(all);

  if (cat) {
    breadcrumb.appendChild(createBreadcrumbSep());

    const catSpan = document.createElement('span');
    catSpan.className = 'breadcrumb-item';
    if (subcat) {
      catSpan.dataset.route = `browser/${cat.id}`;
      catSpan.addEventListener('click', () => renderSubcategoryTabs(cat.id));
    } else {
      catSpan.classList.add('breadcrumb-active');
    }
    catSpan.textContent = cat.name_zh;
    breadcrumb.appendChild(catSpan);
  }

  if (cat && subcat) {
    breadcrumb.appendChild(createBreadcrumbSep());

    const subSpan = document.createElement('span');
    subSpan.className = 'breadcrumb-item breadcrumb-active';
    subSpan.textContent = subcat.name_zh;
    breadcrumb.appendChild(subSpan);
  }
}

function createBreadcrumbSep() {
  const sep = document.createElement('span');
  sep.className = 'breadcrumb-sep';
  sep.textContent = '>';
  return sep;
}

/**
 * 显示浏览区（搜索清除时调用）
 */
export function showBrowser() {
  browserRoot.classList.remove('hidden');
}

/**
 * 隐藏浏览区
 */
export function hideBrowser() {
  browserRoot.classList.add('hidden');
}

/* ----- 通用工具 ----- */

function createPlaceholderSVG(alt, size) {
  const raw = alt || '?';
  const firstChar = raw[0] || '?';
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', size);
  svg.setAttribute('height', size);
  svg.setAttribute('viewBox', '0 0 32 32');
  const rect = document.createElementNS(ns, 'rect');
  rect.setAttribute('width', '32');
  rect.setAttribute('height', '32');
  rect.setAttribute('rx', '4');
  rect.setAttribute('fill', '#dbd8d0');
  svg.appendChild(rect);
  const text = document.createElementNS(ns, 'text');
  text.setAttribute('x', '16');
  text.setAttribute('y', '21');
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('font-size', '14');
  text.setAttribute('fill', '#9a9a9a');
  text.setAttribute('font-family', 'sans-serif');
  text.textContent = firstChar;
  svg.appendChild(text);
  return svg;
}

function createItemIcon(url, alt, size) {
  const rawAlt = alt || '?';
  if (!url || typeof url !== 'string' || !url.trim()) return createPlaceholderSVG(rawAlt, size);
  const img = document.createElement('img');
  img.src = url.trim();
  img.alt = rawAlt;
  img.width = size;
  img.height = size;
  img.onerror = function() { this.replaceWith(createPlaceholderSVG(rawAlt, size)); };
  return img;
}

function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str == null ? '' : String(str);
  return div.innerHTML;
}
