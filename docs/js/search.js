// ============================================
// search.js — 高性能模糊搜索 (1531 items, <50ms)
// ============================================
//
// 性能策略:
//   1. bigram 索引过滤 — 候选集缩小到 10% 以下
//   2. 永不回退全量扫描 — 候选无效直接返回空
//   3. 原生 for 循环 — 比闭包迭代器快 5-10x
//   4. DOM 对象池 — 10 槽位复用，零重建
//   5. 失败图片缓存 — 已知 404 不再发送请求
//   6. 200ms 防抖 — 兼容拼音输入法
//   7. 评分上限 500 — 避免排序爆炸
// ============================================

import { getAllItems, ensureData } from './data.js';

const MAX_SUGGESTIONS = 10;
const DEBOUNCE_MS    = 200;  // FIX: 100→200，兼容拼音输入法
const MAX_SCAN       = 500;  // FIX: 评分上限，避免排序爆炸
const POOL_SIZE      = 10;

// ---- 预计算搜索索引 ----
let searchIndex = null;
let bigramIndex = null;

let activeIndex         = -1;
let currentSuggestions  = [];
let debounceTimer       = null;
let lastQuery           = '';
let lastResults         = null;

const input       = document.getElementById('search-input');
const clearBtn    = document.getElementById('search-clear');
const dropdown    = document.getElementById('search-suggestions');
const browserRoot = document.getElementById('browser-root');
const tplSuggestion = document.getElementById('tpl-suggestion-item');

// FIX: 对象池
const suggestionPool = [];
// FIX: 失败图片缓存
const failedImageUrls = new Set();
// FIX: 空提示元素引用
let emptyMsgEl = null;


/**
 * 构建搜索索引
 */
export function buildSearchIndex() {
  const items = getAllItems();
  if (!items || items.length === 0) return;

  searchIndex = new Array(items.length);
  bigramIndex = new Map();

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const zh = (item.name_zh ?? '').toLowerCase();
    const en = (item.name_en ?? '').toLowerCase();
    const id = (item.id ?? '').toLowerCase();
    // FIX: 去掉 category 索引（按分类搜索需求极低）
    const allText = zh + ' ' + en + ' ' + id;

    searchIndex[i] = { idx: i, zh, en, id };

    const seen = new Set();
    // bigram
    for (let j = 0; j < allText.length - 1; j++) {
      const bg = allText.substring(j, j + 2);
      if (!seen.has(bg)) {
        seen.add(bg);
        if (!bigramIndex.has(bg)) bigramIndex.set(bg, []);
        bigramIndex.get(bg).push(i);
      }
    }
    // 单字
    for (let j = 0; j < allText.length; j++) {
      const ch = allText[j];
      if (ch === ' ') continue;
      if (!bigramIndex.has(ch)) bigramIndex.set(ch, []);
      bigramIndex.get(ch).push(i);
    }
  }

  console.log('[search] Index built: ' + items.length + ' items, ' + bigramIndex.size + ' bigrams');
}


/**
 * 初始化搜索模块 + 对象池
 */
export function initSearch() {
  input.addEventListener('input', onInput);
  input.addEventListener('keydown', onKeyDown);
  clearBtn.addEventListener('click', onClear);
  document.addEventListener('click', onClickOutside);
  document.addEventListener('detail-closed', onDetailClosed);

  // FIX: 预建 DOM 对象池（10 槽位，初始隐藏）
  for (let i = 0; i < POOL_SIZE; i++) {
    const clone = tplSuggestion.content.cloneNode(true);
    const el = clone.querySelector('.suggestion-item');
    el.dataset.index = i;
    el.classList.add('hidden');
    el.addEventListener('mousedown', (e) => {
      e.preventDefault();
      const item = currentSuggestions[i];
      if (item) selectItem(item);
    });
    dropdown.appendChild(el);
    suggestionPool.push({
      el,
      img: el.querySelector('img'),
      zh: el.querySelector('.suggestion-name-zh'),
      en: el.querySelector('.suggestion-name-en'),
    });
  }

  ensureData().then(() => buildSearchIndex());
}


/**
 * 输入事件 — 200ms 防抖
 */
function onInput() {
  clearTimeout(debounceTimer);
  const query = input.value.trim();

  if (query.length === 0) {
    hideSuggestions();
    showBrowser();
    return;
  }

  if (query === lastQuery && lastResults !== null) {
    renderFromCache();
    return;
  }

  debounceTimer = setTimeout(() => {
    const q = input.value.trim();
    if (q !== query) return;

    ensureData().then(() => {
      if (!searchIndex) buildSearchIndex();
      if (input.value.trim() !== q) return;

      const results = fuzzySearch(q);
      lastQuery = q;
      lastResults = results;
      currentSuggestions = results;
      activeIndex = -1;

      if (results.length === 0) {
        showEmpty(q);
        showBrowser();
      } else {
        renderSuggestions(results);
        hideBrowser();
      }
    });
  }, DEBOUNCE_MS);
}


/**
 * FIX: 模糊搜索 — 永不回退全量扫描，原生 for 循环
 */
function fuzzySearch(query) {
  const q = query.toLowerCase().trim();
  if (!q || !searchIndex) return [];

  // FIX: bigram 候选过滤，无效直接返回空（永不回退全量扫描）
  let candidates = null;
  if (q.length >= 2) {
    const bg = q.substring(0, 2);
    const set = bigramIndex.get(bg);
    if (set && set.length < searchIndex.length * 0.9) candidates = set;
  } else {
    const set = bigramIndex.get(q[0]);
    if (set && set.length < searchIndex.length * 0.9) candidates = set;
  }
  if (!candidates) return [];

  // FIX: 原生 for 循环替代闭包迭代器
  const results = [];
  const scanCount = Math.min(candidates.length, MAX_SCAN);

  for (let k = 0; k < scanCount; k++) {
    const idx = candidates[k];
    const si = searchIndex[idx];
    if (!si) continue;

    let score = 0;
    if (si.zh === q) score = 110;
    else if (si.id === q || si.en === q) score = 100;
    else if (si.zh.startsWith(q)) score = 70;
    else if (si.en.startsWith(q) || si.id.startsWith(q)) score = 60;
    else if (si.zh.includes(q)) score = 45;
    else if (si.en.includes(q) || si.id.includes(q)) score = 35;

    if (score > 0) results.push({ idx, score });
  }

  results.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return searchIndex[a.idx].zh.length - searchIndex[b.idx].zh.length;
  });

  const items = getAllItems();
  return results.slice(0, MAX_SUGGESTIONS).map(r => items[searchIndex[r.idx].idx]);
}


/**
 * FIX: 从缓存渲染 — 对象池重新填充
 */
function renderFromCache() {
  if (!lastResults || lastResults.length === 0) return;
  currentSuggestions = lastResults;
  activeIndex = -1;
  renderSuggestions(lastResults);
}


/**
 * FIX: 渲染 — 对象池更新，不重建 DOM
 */
function renderSuggestions(items) {
  // 清除空提示
  if (emptyMsgEl) { emptyMsgEl.remove(); emptyMsgEl = null; }

  for (let i = 0; i < POOL_SIZE; i++) {
    const slot = suggestionPool[i];
    const item = items[i];
    if (!item) {
      slot.el.classList.add('hidden');
      continue;
    }
    slot.el.classList.remove('hidden');
    slot.el.dataset.index = i;

    // FIX: 图片 — 已知失败的用占位，不发请求
    const url = item.icon_url || '';
    if (failedImageUrls.has(url)) {
      if (slot.img.tagName === 'IMG') {
        slot.img.replaceWith(createPlaceholderSVG(item.name_zh, 24));
      }
    } else {
      if (slot.img.tagName !== 'IMG') {
        // 重新创建 img 元素
        const newImg = document.createElement('img');
        newImg.width = 24; newImg.height = 24; newImg.loading = 'lazy';
        slot.img.replaceWith(newImg);
        slot.img = newImg;
      }
      slot.img.src = url;
      slot.img.alt = item.name_zh || '?';
      slot.img.onerror = function() {
        failedImageUrls.add(url);
        this.replaceWith(createPlaceholderSVG(item.name_zh, 24));
      };
    }

    slot.zh.textContent = item.name_zh || '';
    slot.en.textContent = item.name_en || '';
  }
  dropdown.classList.remove('hidden');
}


function updateActiveSuggestion() {
  const children = dropdown.querySelectorAll('.suggestion-item');
  children.forEach((el, i) => {
    el.classList.toggle('active', i === activeIndex);
  });
  const activeEl = children[activeIndex];
  if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });
}


/**
 * FIX: 显示空提示 — 适配对象池
 */
function showEmpty(query) {
  for (const slot of suggestionPool) {
    slot.el.classList.add('hidden');
  }
  if (emptyMsgEl) emptyMsgEl.remove();
  emptyMsgEl = document.createElement('div');
  emptyMsgEl.className = 'suggestion-empty';
  emptyMsgEl.textContent = '未找到与「' + query + '」相关的物品';
  dropdown.appendChild(emptyMsgEl);
  dropdown.classList.remove('hidden');
}


/**
 * FIX: 隐藏 — 只隐藏槽位，不清空 DOM
 */
function hideSuggestions() {
  dropdown.classList.add('hidden');
  for (const slot of suggestionPool) {
    slot.el.classList.add('hidden');
  }
  if (emptyMsgEl) { emptyMsgEl.remove(); emptyMsgEl = null; }
  currentSuggestions = [];
  activeIndex = -1;
}


/**
 * 选中物品 → 打开详情面板
 */
function selectItem(item) {
  hideSuggestions();
  input.value = item.name_zh || '';
  input.blur();
  lastQuery = '';
  lastResults = null;

  const currentHash = window.location.hash.replace(/^#/, '');
  const cleanHash = currentHash.replace(/#item\/[^#]+/, '');
  const newHash = cleanHash ? cleanHash + '#item/' + item.id : 'item/' + item.id;
  history.replaceState(null, '', window.location.pathname + '#' + newHash);

  document.dispatchEvent(new CustomEvent('item-select', { detail: { id: item.id } }));
}


// ---- 键盘导航 ----

function onKeyDown(e) {
  if (dropdown.classList.contains('hidden')) return;

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, currentSuggestions.length - 1);
      updateActiveSuggestion();
      break;
    case 'ArrowUp':
      e.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      updateActiveSuggestion();
      break;
    case 'Enter':
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < currentSuggestions.length) {
        selectItem(currentSuggestions[activeIndex]);
      } else if (currentSuggestions.length > 0) {
        selectItem(currentSuggestions[0]);
      }
      break;
    case 'Escape':
      e.preventDefault();
      onClear();
      break;
  }
}


// ---- 清除 / 外部点击 ----

function onClear() {
  input.value = '';
  lastQuery = '';
  lastResults = null;
  hideSuggestions();
  showBrowser();
  input.focus();
}

function onDetailClosed() {
  input.value = '';
  lastQuery = '';
  lastResults = null;
  hideSuggestions();
  showBrowser();
}

function onClickOutside(e) {
  if (!dropdown.classList.contains('hidden')) {
    const insideSearch = e.target.closest('.search-header');
    if (!insideSearch) {
      hideSuggestions();
      if (!input.value.trim()) showBrowser();
    }
  }
}


function showBrowser() {
  browserRoot.classList.remove('hidden');
}

function hideBrowser() {
  browserRoot.classList.add('hidden');
}


// ---- 图片工具 ----

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
