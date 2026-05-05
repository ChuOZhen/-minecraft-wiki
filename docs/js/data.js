// ============================================
// data.js — 数据加载、缓存、查询接口
// ============================================

let data = null;
let itemsMap = null;
let loading = false;
let loadPromise = null;

// JEI 级依赖图：反向索引
let productIndex = null;   // result_id → [{ itemId, recipe }]
let ingredientIndex = null; // ingredient_id → [{ itemId, recipe }]

const DATA_PATH = './data/data.json';
const FALLBACK_PATH = './data/data_fallback.json';

/**
 * 加载数据（带缓存，只请求一次）
 */
async function loadData() {
  if (data) return data;
  if (loadPromise) return loadPromise;

  loading = true;
  loadPromise = fetchData();

  try {
    data = await loadPromise;
  } finally {
    loading = false;
  }

  buildIndex();
  return data;
}

async function fetchData() {
  try {
    const resp = await fetch(DATA_PATH);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.warn('主数据加载失败，尝试兜底数据:', err.message);
    try {
      const resp = await fetch(FALLBACK_PATH);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (fbErr) {
      console.error('兜底数据加载也失败:', fbErr.message);
      return { meta: { version: 'fallback' }, categories: [], items: [] };
    }
  }
}

/**
 * 构建 items 的 id 索引
 */
function buildIndex() {
  if (!data || !data.items) return;
  itemsMap = new Map();
  productIndex = new Map();
  ingredientIndex = new Map();

  for (const item of data.items) {
    itemsMap.set(item.id, item);

    // 遍历所有 crafting 配方
    const recipes = item.crafting ?? [];
    for (const recipe of recipes) {
      const resultId = recipe.result_id ?? item.id;

      // 产品索引：result_id → 谁合成了它
      if (!productIndex.has(resultId)) {
        productIndex.set(resultId, []);
      }
      productIndex.get(resultId).push({ itemId: item.id, recipe });

      // 原料索引：每个 ingredient → 被哪些配方使用
      for (const ingId of Object.keys(recipe.ingredients ?? {})) {
        if (!ingredientIndex.has(ingId)) {
          ingredientIndex.set(ingId, []);
        }
        const existing = ingredientIndex.get(ingId).find(e => e.itemId === item.id);
        if (!existing) {
          ingredientIndex.get(ingId).push({ itemId: item.id, recipe });
        }
      }
    }

    // 烧炼配方：输入物品 → 当前物品
    const smelting = item.acquisition?.smelting;
    if (smelting?.input_id) {
      if (!ingredientIndex.has(smelting.input_id)) {
        ingredientIndex.set(smelting.input_id, []);
      }
      ingredientIndex.get(smelting.input_id).push({
        itemId: item.id,
        recipe: { type: 'smelting', input_id: smelting.input_id, result_id: item.id }
      });
    }
  }
}

/**
 * JEI 查询：哪些配方合成了这个物品？（来源查询）
 * 返回所有 result_id === 该物品的 recipe 列表
 */
export function getCraftingSources(itemId) {
  if (!productIndex) return [];
  return productIndex.get(itemId) ?? [];
}

/**
 * JEI 查询：这个物品被哪些配方使用？（用途查询）
 * 返回所有以该物品为原料的 recipe 列表
 */
export function getCraftingUses(itemId) {
  if (!ingredientIndex) return [];
  return ingredientIndex.get(itemId) ?? [];
}

/**
 * 查询物品的关系图谱（来源 + 用途）
 */
export function getItemRelations(itemId) {
  return {
    sources: getCraftingSources(itemId),
    uses: getCraftingUses(itemId),
  };
}

/**
 * 获取所有物品（返回数组）
 */
export function getAllItems() {
  if (!data || !data.items) return [];
  return data.items;
}

/**
 * 根据 ID 获取单个物品
 */
export function getItemById(id) {
  if (!itemsMap) return null;
  return itemsMap.get(id) || null;
}

/**
 * 获取所有分类（大类列表，含小类）
 */
export function getCategories() {
  if (!data || !data.categories) return [];
  return data.categories;
}

/**
 * 获取某个大类下的小类列表
 */
export function getSubcategories(categoryId) {
  const cat = getCategoryById(categoryId);
  return cat ? cat.subcategories : [];
}

/**
 * 根据大类 ID 获取大类信息
 */
export function getCategoryById(categoryId) {
  if (!data || !data.categories) return null;
  return data.categories.find(c => c.id === categoryId) || null;
}

/**
 * 获取某个小类下的所有物品
 */
export function getItemsBySubcategory(categoryId, subcategoryId) {
  if (!data || !data.items) return [];
  return data.items.filter(
    item => item.category === categoryId && item.subcategory === subcategoryId
  );
}

/**
 * 获取某个大类下的所有物品
 */
export function getItemsByCategory(categoryId) {
  if (!data || !data.items) return [];
  return data.items.filter(item => item.category === categoryId);
}

/**
 * 数据是否已加载
 */
export function isDataReady() {
  return data !== null;
}

/**
 * 是否正在加载
 */
export function isLoading() {
  return loading;
}

/**
 * 确保数据已加载（供需要等待数据的模块调用）
 */
export function ensureData() {
  return loadData();
}
