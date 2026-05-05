// ============================================
// detail.js — 物品详情侧边栏（渲染、关闭、URL 同步）
//   P0 fix: defensive rendering, image fallback, safe access
// ============================================

import { getItemById, getCategoryById, ensureData, getCraftingSources, getCraftingUses } from './data.js';

const panel        = document.getElementById('detail-panel');
const overlay      = document.getElementById('detail-overlay');
const closeBtn     = document.getElementById('detail-close');
const detailBody   = document.getElementById('detail-body');

let currentItemId  = null;
let isOpen         = false;
let closeTimer     = null;

/**
 * 初始化详情模块
 */
export function initDetail() {
  closeBtn.addEventListener('click', closePanel);
  overlay.addEventListener('click', closePanel);
  document.addEventListener('keydown', onKeyDown);
  document.addEventListener('item-select', onItemSelect);
}

/**
 * 响应物品选中事件
 */
function onItemSelect(e) {
  ensureData().then(() => {
    openPanel(e.detail.id);
  });
}

/**
 * 打开详情面板
 */
export function openPanel(itemId) {
  const item = getItemById(itemId);
  if (!item) return;

  currentItemId = itemId;
  renderDetail(item);
  showPanel();
}

/**
 * 关闭详情面板
 */
export function closePanel() {
  if (!isOpen) return;
  isOpen = false;
  currentItemId = null;

  // 动画
  panel.classList.add('closing');
  overlay.style.animation = 'overlayFadeOut 0.25s forwards';

  clearTimeout(closeTimer);
  closeTimer = setTimeout(() => {
    panel.classList.add('hidden');
    panel.classList.remove('closing');
    overlay.classList.add('hidden');
    overlay.style.animation = '';
    detailBody.innerHTML = '';
    // 通知搜索模块恢复浏览区
    document.dispatchEvent(new CustomEvent('detail-closed'));
  }, 250);

  // 清除 URL 中的 item hash
  removeItemFromHash();
}

/**
 * 键盘事件
 */
function onKeyDown(e) {
  if (e.key === 'Escape' && isOpen) {
    e.preventDefault();
    closePanel();
  }
}

// ============================================
// 面板显示/隐藏
// ============================================

function showPanel() {
  clearTimeout(closeTimer);

  panel.classList.remove('hidden', 'closing');
  overlay.classList.remove('hidden');
  overlay.style.animation = '';
  isOpen = true;
}

// ============================================
// 详情渲染
// ============================================

function renderDetail(item) {
  detailBody.innerHTML = '';

  // 防御：确保关键字段存在
  if (!Array.isArray(item.crafting)) item.crafting = [];
  if (!item.acquisition || typeof item.acquisition !== 'object') {
    item.acquisition = { methods: ['未知'] };
  }
  const acq = item.acquisition;
  if (!Array.isArray(acq.methods) || acq.methods.length === 0) {
    acq.methods = ['未知'];
  }

  detailBody.appendChild(buildHeader(item));
  detailBody.appendChild(createDivider());

  // 获取方式 — 永远渲染
  detailBody.appendChild(buildAcquisition(item));
  detailBody.appendChild(createDivider());

  // 合成配方（全部展示，UI 区分主配方/副配方）
  if (item.crafting.length > 0) {
    detailBody.appendChild(buildCrafting(item.crafting));
    if (!hasProcessingRecipes(item)) {
      detailBody.appendChild(createDivider());
    }
  } else {
    // 无配方时显示提示
    const emptySection = document.createElement('section');
    emptySection.className = 'detail-section';
    emptySection.innerHTML = '<h3 class="detail-section-title">合成配方</h3>' +
      '<p style="color: var(--text-muted); padding: var(--space-md);">暂无配方</p>';
    detailBody.appendChild(emptySection);
    detailBody.appendChild(createDivider());
  }

  // JEI 级：来源查询（谁合成了这个物品）
  const sources = getCraftingSources(item.id);
  if (sources.length > 0) {
    detailBody.appendChild(buildSourceList(sources, item.id));
    detailBody.appendChild(createDivider());
  }

  // JEI 级：用途查询（这个物品被用于合成什么）
  const uses = getCraftingUses(item.id);
  if (uses.length > 0) {
    detailBody.appendChild(buildUseList(uses, item.id));
    detailBody.appendChild(createDivider());
  }

  // 加工配方（烧炼/切石/锻造）
  if (hasProcessingRecipes(item)) {
    const ps = buildProcessing(item);
    if (ps) detailBody.appendChild(ps);
    detailBody.appendChild(createDivider());
  }

  // 自然生成
  const natGen = acq.natural_generation;
  if (Array.isArray(natGen) && natGen.length > 0) {
    detailBody.appendChild(buildNaturalGeneration(natGen));
    detailBody.appendChild(createDivider());
  }

  // 相关物品
  const related = item.related_items;
  if (Array.isArray(related) && related.length > 0) {
    const seen = new Set();
    const valid = related.filter(id => {
      if (!id || seen.has(id)) return false;
      if (!getItemById(id)) return false;
      seen.add(id);
      return true;
    });
    if (valid.length > 0) {
      detailBody.appendChild(buildRelatedItems(valid));
    }
  }
}

// ============================================
// 头部：图标 + 名称 + ID + 标签
// ============================================

function buildHeader(item) {
  const section = document.createElement('div');
  section.className = 'detail-header';

  const cat = getCategoryById(item.category ?? 'miscellaneous');
  const subcats = cat?.subcategories ?? [];
  let subcatName = '';
  for (const s of subcats) {
    if (s.id === item.subcategory) { subcatName = s.name_zh; break; }
  }

  const nameZh  = item.name_zh ?? item.name_en ?? item.id ?? '未知物品';
  const nameEn  = item.name_en ?? item.id ?? '';
  const itemId  = item.id ?? '';
  const catName = cat?.name_zh ?? item.category ?? '—';
  const subName = subcatName || item.subcategory || '—';

  // FIX: DOM 版图标 — 100% 可靠 onerror 绑定，永不空白
  section.appendChild(createItemIcon(item.icon_url, nameZh, 64));

  const namesDiv = document.createElement('div');
  namesDiv.className = 'detail-names';
  namesDiv.innerHTML = `
    <h2 class="detail-name-zh">${escapeHTML(nameZh)}</h2>
    <p class="detail-name-en">${escapeHTML(nameEn)}</p>
    <p class="detail-id">${escapeHTML(itemId)}</p>
    <div class="detail-tags">
      <span class="detail-tag">${escapeHTML(catName)}</span>
      <span class="detail-tag">${escapeHTML(subName)}</span>
    </div>
  `;
  section.appendChild(namesDiv);

  return section;
}

// ============================================
// 获取方式
// ============================================

function buildAcquisition(item) {
  const section = document.createElement('section');
  section.className = 'detail-section';

  const acq = item.acquisition ?? {};
  const methods = Array.isArray(acq.methods) && acq.methods.length > 0
    ? acq.methods
    : ['未知'];

  let html = '<h3 class="detail-section-title">获取方式</h3><ul class="acquisition-list">';
  for (const method of methods) {
    html += `<li class="acquisition-item">${escapeHTML(String(method))}</li>`;
  }
  html += '</ul>';

  // 交易信息
  if (acq.trading) {
    html += `<div class="acquisition-extra">${escapeHTML(String(acq.trading))}</div>`;
  }

  // 掉落来源
  const drops = acq.drops_from;
  if (Array.isArray(drops) && drops.length > 0) {
    html += '<div class="acquisition-extra">掉落来源：' +
      drops.map(d => escapeHTML(String(d))).join('、') + '</div>';
  }

  section.innerHTML = html;
  return section;
}

// ============================================
// 合成配方 3×3 网格
// ============================================

function buildCrafting(recipes) {
  const section = document.createElement('section');
  section.className = 'detail-section';
  section.id = 'detail-section-crafting';

  section.innerHTML = '<h3 class="detail-section-title">合成配方</h3>';
  const container = document.createElement('div');
  container.className = 'crafting-recipes';

  for (const recipe of recipes) {
    container.appendChild(buildSingleCraftingRecipe(recipe));
  }

  section.appendChild(container);

  // 绑定配方格内图标点击（跳转到对应物品详情）
  section.querySelectorAll('.crafting-cell[data-item-id]').forEach(cell => {
    cell.addEventListener('click', () => {
      const id = cell.dataset.itemId;
      if (id) {
        document.dispatchEvent(new CustomEvent('item-select', { detail: { id } }));
      }
    });
    cell.style.cursor = 'pointer';
    cell.title = '点击查看详情';
  });

  return section;
}

function buildSingleCraftingRecipe(recipe) {
  // FIX: 全 DOM 构建，不拼接 HTML 字符串，确保 onerror 正确绑定
  const wrapper = document.createElement('div');
  wrapper.className = 'crafting-recipe';

  // 3×3 网格
  const grid = document.createElement('div');
  grid.className = 'crafting-grid';

  const pattern = Array.isArray(recipe.pattern) ? recipe.pattern : [['','',''],['','',''],['','','']];
  const ingredients = recipe.ingredients ?? {};

  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 3; col++) {
      const key = (pattern[row] && pattern[row][col] && typeof pattern[row][col] === 'string')
        ? pattern[row][col].trim() : '';

      const cell = document.createElement('div');

      if (key && ingredients[key]) {
        const ing = ingredients[key];
        cell.className = 'crafting-cell';
        if (ing.id) {
          cell.dataset.itemId = ing.id;
        }
        // FIX: DOM 版图标，null/空字符串自动 → SVG placeholder
        cell.appendChild(createItemIcon(ing.icon_url, ing.name_zh ?? key, 32));
        const count = ing.count ?? 1;
        if (count > 1) {
          const countSpan = document.createElement('span');
          countSpan.className = 'crafting-cell-count';
          countSpan.textContent = count;
          cell.appendChild(countSpan);
        }
      } else {
        // FIX: pattern 中有 key 但 ingredients 缺失 → warn
        if (key && !ingredients[key]) {
          console.warn('Recipe ingredient key missing in ingredients:', key, 'recipe:', recipe.result_id);
        }
        cell.className = 'crafting-cell empty';
      }

      grid.appendChild(cell);
    }
  }

  wrapper.appendChild(grid);

  // 箭头
  const arrow = document.createElement('div');
  arrow.className = 'crafting-arrow';
  arrow.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>';
  wrapper.appendChild(arrow);

  // 结果
  const resultDiv = document.createElement('div');
  resultDiv.className = 'crafting-result';
  // FIX: null/空字符串 → SVG placeholder
  resultDiv.appendChild(createItemIcon(recipe.result_icon, '', 40));

  const resultInfo = document.createElement('div');
  resultInfo.className = 'crafting-result-info';
  const resultItem = recipe.result_id ? getItemById(recipe.result_id) : null;
  const count = (recipe.result_count ?? 1);
  resultInfo.innerHTML = `<span class="crafting-result-name">${escapeHTML(resultItem?.name_zh ?? '')}</span>${count > 1 ? `<span class="crafting-result-count">×${count}</span>` : ''}`;
  resultDiv.appendChild(resultInfo);
  wrapper.appendChild(resultDiv);

  // 配方类型标签 + 主/副标记
  const isPrimary = recipe.is_primary_recipe ?? recipe.result_match ?? true;
  const typeLabel = recipe.shaped === false ? '无序合成' :
    (recipe.type === 'stonecutting' ? '切石机' : '工作台');
  const typeSpan = document.createElement('span');
  typeSpan.className = isPrimary ? 'crafting-type' : 'crafting-type crafting-type-secondary';
  typeSpan.textContent = isPrimary ? typeLabel : typeLabel + ' (原料)';
  wrapper.appendChild(typeSpan);

  return wrapper;
}

// ============================================
// 加工配方（烧炼 / 切石 / 锻造）
// ============================================

function hasProcessingRecipes(item) {
  const a = item.acquisition;
  const hasSmelting = a && typeof a === 'object' && Array.isArray(a.smelting) && a.smelting.length > 0;
  const hasStonecutting = Array.isArray(item.stonecutting) && item.stonecutting.length > 0;
  const hasSmithing = Array.isArray(item.smithing) && item.smithing.length > 0;
  return hasSmelting || hasStonecutting || hasSmithing;
}

function buildProcessing(item) {
  const acq = item.acquisition ?? {};
  const smeltingRecipes = Array.isArray(acq.smelting) ? acq.smelting : [];
  const stonecuttingRecipes = Array.isArray(item.stonecutting) ? item.stonecutting : [];
  const smithingRecipes = Array.isArray(item.smithing) ? item.smithing : [];

  if (smeltingRecipes.length === 0 && stonecuttingRecipes.length === 0 && smithingRecipes.length === 0) {
    return null;
  }

  const section = document.createElement('section');
  section.className = 'detail-section';

  section.innerHTML = '<h3 class="detail-section-title">加工配方</h3>';
  const container = document.createElement('div');
  container.className = 'processing-recipes';

  for (const recipe of smeltingRecipes) {
    container.appendChild(buildSmeltingRecipe(recipe));
  }
  for (const recipe of stonecuttingRecipes) {
    container.appendChild(buildStonecuttingRecipe(recipe));
  }
  for (const recipe of smithingRecipes) {
    container.appendChild(buildSmithingRecipe(recipe));
  }

  section.appendChild(container);
  return section;
}

function buildSmeltingRecipe(recipe) {
  // FIX: 全 DOM 构建
  const wrapper = document.createElement('div');
  wrapper.className = 'processing-recipe';

  // Input
  const inputDiv = document.createElement('div');
  inputDiv.className = 'processing-input';
  inputDiv.appendChild(createItemIcon(recipe.input_icon, recipe.input_id || '', 40));
  const inputLabel = document.createElement('span');
  inputLabel.className = 'processing-label';
  inputLabel.textContent = '输入';
  inputDiv.appendChild(inputLabel);
  wrapper.appendChild(inputDiv);

  // Arrow + Fuel
  const arrow1 = document.createElement('div');
  arrow1.className = 'processing-arrow';
  arrow1.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>';
  wrapper.appendChild(arrow1);

  const fuelDiv = document.createElement('div');
  fuelDiv.className = 'processing-fuel';
  fuelDiv.textContent = recipe.fuel || '任意燃料';
  wrapper.appendChild(fuelDiv);

  // Arrow + Output
  const arrow2 = document.createElement('div');
  arrow2.className = 'processing-arrow';
  arrow2.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>';
  wrapper.appendChild(arrow2);

  const outputDiv = document.createElement('div');
  outputDiv.className = 'processing-output';
  outputDiv.appendChild(createItemIcon(recipe.output_icon, recipe.output_id || '', 40));
  const outputLabel = document.createElement('span');
  outputLabel.className = 'processing-label';
  outputLabel.textContent = '输出 ×' + (recipe.output_count || 1);
  outputDiv.appendChild(outputLabel);
  wrapper.appendChild(outputDiv);

  // Meta
  if (recipe.experience != null || recipe.cook_time_seconds != null) {
    const meta = document.createElement('div');
    meta.className = 'processing-meta';
    const parts = [];
    if (recipe.experience != null) parts.push('经验值：' + recipe.experience);
    if (recipe.cook_time_seconds != null) parts.push('烧炼时间：' + recipe.cook_time_seconds + '秒');
    meta.textContent = parts.join(' ');
    wrapper.appendChild(meta);
  }

  return wrapper;
}

function buildStonecuttingRecipe(recipe) {
  // FIX: 全 DOM 构建
  const wrapper = document.createElement('div');
  wrapper.className = 'processing-recipe';

  const label = document.createElement('span');
  label.className = 'processing-label';
  label.textContent = '切石机';
  wrapper.appendChild(label);

  const flow = document.createElement('div');
  flow.className = 'processing-flow';

  // Input
  const inputDiv = document.createElement('div');
  inputDiv.className = 'processing-input';
  inputDiv.appendChild(createItemIcon(recipe.input_icon, recipe.input_id || '', 40));
  const inputLabel = document.createElement('span');
  inputLabel.className = 'processing-label';
  inputLabel.textContent = recipe.input_id || '';
  inputDiv.appendChild(inputLabel);
  flow.appendChild(inputDiv);

  // Arrow
  const arrow = document.createElement('div');
  arrow.className = 'processing-arrow';
  arrow.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>';
  flow.appendChild(arrow);

  // Output
  const outputDiv = document.createElement('div');
  outputDiv.className = 'processing-output';
  outputDiv.appendChild(createItemIcon(recipe.output_icon, recipe.output_id || '', 40));
  const outputLabel = document.createElement('span');
  outputLabel.className = 'processing-label';
  outputLabel.textContent = '×' + (recipe.output_count || 1);
  outputDiv.appendChild(outputLabel);
  flow.appendChild(outputDiv);

  wrapper.appendChild(flow);
  return wrapper;
}

function buildSmithingRecipe(recipe) {
  // FIX: 全 DOM 构建
  const wrapper = document.createElement('div');
  wrapper.className = 'processing-recipe';

  const label = document.createElement('span');
  label.className = 'processing-label';
  label.textContent = '锻造台';
  wrapper.appendChild(label);

  const slots = document.createElement('div');
  slots.className = 'smithing-slots';

  // Template
  const templateSlot = document.createElement('div');
  templateSlot.className = 'smithing-slot';
  const templateLabel = document.createElement('span');
  templateLabel.className = 'smithing-slot-label';
  templateLabel.textContent = '模板';
  templateSlot.appendChild(templateLabel);
  templateSlot.appendChild(createItemIcon(recipe.template_icon, recipe.template_id || '', 32));
  const templateName = document.createElement('span');
  templateName.className = 'processing-label';
  templateName.textContent = recipe.template_id || '';
  templateSlot.appendChild(templateName);
  slots.appendChild(templateSlot);

  // Base
  const baseSlot = document.createElement('div');
  baseSlot.className = 'smithing-slot';
  const baseLabel = document.createElement('span');
  baseLabel.className = 'smithing-slot-label';
  baseLabel.textContent = '基底';
  baseSlot.appendChild(baseLabel);
  baseSlot.appendChild(createItemIcon(recipe.base_icon, recipe.base_id || '', 32));
  const baseName = document.createElement('span');
  baseName.className = 'processing-label';
  baseName.textContent = recipe.base_id || '';
  baseSlot.appendChild(baseName);
  slots.appendChild(baseSlot);

  // Addition
  const additionSlot = document.createElement('div');
  additionSlot.className = 'smithing-slot';
  const additionLabel = document.createElement('span');
  additionLabel.className = 'smithing-slot-label';
  additionLabel.textContent = '添加';
  additionSlot.appendChild(additionLabel);
  additionSlot.appendChild(createItemIcon(recipe.addition_icon, recipe.addition_id || '', 32));
  const additionName = document.createElement('span');
  additionName.className = 'processing-label';
  additionName.textContent = recipe.addition_id || '';
  additionSlot.appendChild(additionName);
  slots.appendChild(additionSlot);

  // Arrow
  const arrow = document.createElement('div');
  arrow.className = 'processing-arrow';
  arrow.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>';
  slots.appendChild(arrow);

  // Output
  const outputDiv = document.createElement('div');
  outputDiv.className = 'processing-output';
  outputDiv.appendChild(createItemIcon(recipe.output_icon, recipe.output_id || '', 40));
  const outputLabel = document.createElement('span');
  outputLabel.className = 'processing-label';
  outputLabel.textContent = '×' + (recipe.output_count || 1);
  outputDiv.appendChild(outputLabel);
  slots.appendChild(outputDiv);

  wrapper.appendChild(slots);
  return wrapper;
}

// ============================================
// 自然生成
// ============================================

function buildNaturalGeneration(locations) {
  const section = document.createElement('section');
  section.className = 'detail-section';
  section.id = 'detail-section-natural';

  let html = '<h3 class="detail-section-title">自然生成</h3><ul class="natural-list">';
  for (const loc of locations) {
    html += `<li>${escapeHTML(String(loc))}</li>`;
  }
  html += '</ul>';

  section.innerHTML = html;
  return section;
}

// ============================================
// 相关物品
// ============================================

function buildRelatedItems(relatedIds) {
  const section = document.createElement('section');
  section.className = 'detail-section';
  section.id = 'detail-section-related';

  section.innerHTML = '<h3 class="detail-section-title">相关物品</h3>';
  const container = document.createElement('div');
  container.className = 'related-items';

  for (const id of relatedIds) {
    const rel = getItemById(id);
    if (!rel) continue;
    const itemDiv = document.createElement('div');
    itemDiv.className = 'related-item';
    itemDiv.dataset.itemId = id;
    // FIX: DOM 版图标
    itemDiv.appendChild(createItemIcon(rel.icon_url, rel.name_zh, 32));
    const nameSpan = document.createElement('span');
    nameSpan.className = 'related-item-name';
    nameSpan.textContent = rel.name_zh;
    itemDiv.appendChild(nameSpan);
    container.appendChild(itemDiv);
  }

  section.appendChild(container);

  // 点击相关物品跳转
  section.querySelectorAll('.related-item').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.dataset.itemId;
      if (id) {
        document.dispatchEvent(new CustomEvent('item-select', { detail: { id } }));
      }
    });
  });

  return section;
}

// ============================================
// JEI 查询：来源 & 用途
// ============================================

function buildSourceList(sources, currentItemId) {
  const section = document.createElement('section');
  section.className = 'detail-section';

  section.innerHTML = '<h3 class="detail-section-title">合成来源</h3>';
  const container = document.createElement('div');
  container.className = 'related-items';

  // 去重
  const seen = new Set();
  for (const src of sources) {
    if (seen.has(src.itemId)) continue;
    seen.add(src.itemId);

    const srcItem = getItemById(src.itemId);
    if (!srcItem) continue;
    const itemDiv = document.createElement('div');
    itemDiv.className = 'related-item';
    itemDiv.dataset.itemId = src.itemId;
    // FIX: DOM 版图标
    itemDiv.appendChild(createItemIcon(srcItem.icon_url, srcItem.name_zh ?? srcItem.name_en, 32));
    const nameSpan = document.createElement('span');
    nameSpan.className = 'related-item-name';
    nameSpan.textContent = srcItem.name_zh ?? srcItem.name_en;
    itemDiv.appendChild(nameSpan);
    container.appendChild(itemDiv);
  }

  section.appendChild(container);

  section.querySelectorAll('.related-item').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.dataset.itemId;
      if (id) document.dispatchEvent(new CustomEvent('item-select', { detail: { id } }));
    });
  });

  return section;
}

function buildUseList(uses, currentItemId) {
  const section = document.createElement('section');
  section.className = 'detail-section';

  section.innerHTML = '<h3 class="detail-section-title">可合成为</h3>';
  const container = document.createElement('div');
  container.className = 'related-items';

  const seen = new Set();
  // 优先展示 is_primary_recipe 为 true 的
  const sorted = [...uses].sort((a, b) => {
    const aP = a.recipe?.is_primary_recipe ?? false;
    const bP = b.recipe?.is_primary_recipe ?? false;
    return bP - aP;
  });

  for (const use of sorted) {
    const rid = use.recipe?.result_id;
    if (!rid || seen.has(rid)) continue;
    seen.add(rid);

    const resultItem = getItemById(rid);
    if (!resultItem) continue;
    const primary = use.recipe?.is_primary_recipe;
    const itemDiv = document.createElement('div');
    itemDiv.className = 'related-item' + (primary ? ' related-item-primary' : '');
    itemDiv.dataset.itemId = rid;
    // FIX: DOM 版图标
    itemDiv.appendChild(createItemIcon(resultItem.icon_url, resultItem.name_zh ?? resultItem.name_en, 32));
    const nameSpan = document.createElement('span');
    nameSpan.className = 'related-item-name';
    nameSpan.textContent = resultItem.name_zh ?? resultItem.name_en;
    itemDiv.appendChild(nameSpan);
    container.appendChild(itemDiv);
  }

  section.appendChild(container);

  section.querySelectorAll('.related-item').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.dataset.itemId;
      if (id) document.dispatchEvent(new CustomEvent('item-select', { detail: { id } }));
    });
  });

  return section;
}

// ============================================
// URL Hash 管理
// ============================================

function removeItemFromHash() {
  const hash = window.location.hash;
  if (!hash) return;
  const newHash = hash.replace(/#item\/[^#]+/, '');
  if (newHash === hash) return;
  const url = window.location.pathname + (newHash || '');
  history.replaceState(null, '', url);
}

// ============================================
// 工具
// ============================================

function createDivider() {
  const div = document.createElement('div');
  div.className = 'detail-divider';
  return div;
}

// ============================================
// 图片工具 — 100% DOM，所有图片本地加载，零跨域
// ============================================

/**
 * 创建 SVG 占位图（灰色背景 + 物品名首字符）
 */
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

/**
 * 统一图片创建入口 — 本地路径直连，永不跨域
 */
function createItemIcon(url, alt, size) {
  const rawAlt = alt || '?';

  if (!url || typeof url !== 'string' || !url.trim()) {
    return createPlaceholderSVG(rawAlt, size);
  }

  const img = document.createElement('img');
  img.src = url.trim();
  img.alt = rawAlt;
  img.width = size;
  img.height = size;

  img.onerror = function() {
    this.replaceWith(createPlaceholderSVG(rawAlt, size));
  };

  return img;
}

function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str == null ? '' : String(str);
  return div.innerHTML;
}
