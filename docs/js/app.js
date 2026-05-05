// ============================================
// app.js — 应用入口（初始化、全局工具、协调模块）
// ============================================

import { ensureData, isDataReady, getAllItems } from './data.js';
import { initSearch } from './search.js';
import { initBrowser } from './browser.js';
import { initDetail } from './detail.js';

// ============================================
// 全局工具：图片错误回退（plan.md §6.5）
// ============================================

/**
 * 创建带 onerror 回退的 <img> 元素
 */
window.createItemIcon = function(iconUrl, alt, size = 32) {
  const img = document.createElement('img');
  img.src = iconUrl;
  img.alt = alt || '';
  img.width = size;
  img.height = size;
  img.loading = 'lazy';
  img.onerror = function() {
    this.replaceWith(createPlaceholderIcon(alt, size));
  };
  return img;
};

/**
 * inline onerror 回调：用 SVG 占位图替换破损图片
 * 被 search.js / browser.js / detail.js 的内联 HTML 调用
 */
window.createPlaceholder = function(img, alt, size = 32) {
  return createPlaceholderIcon(alt, Number(size) || 32);
};

function createPlaceholderIcon(alt, size = 32) {
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
  const char = (alt && alt.length > 0) ? alt[0] : '?';
  text.textContent = /[一-鿿]/.test(char) ? char : (char.toUpperCase());
  svg.appendChild(text);

  return svg;
}

// ============================================
// 应用初始化
// ============================================

async function init() {
  // 预加载数据（后台进行，不阻塞 UI 初始化）
  const dataPromise = ensureData();

  // 初始化各模块（不依赖数据即可绑定事件）
  initSearch();
  initDetail();
  initBrowser(); // 内部通过 ensureData 等待

  // 等待数据加载完成
  await dataPromise;

  if (isDataReady()) {
    const count = getAllItems ? getAllItems().length : 0;
    console.log(`Minecraft 物品百科 - 数据就绪，共 ${count} 个物品。可通过搜索或浏览开始使用。`);
  } else {
    console.warn('数据加载失败，部分功能可能不可用。请检查 data.json 或 data_fallback.json。');
  }
}

// 启动
init();
