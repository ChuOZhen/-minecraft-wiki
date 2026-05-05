# 我的世界物品百科网站 - 完整构建计划 v2.0

> **文档用途**：本计划文档是项目的唯一权威规格说明，描述精准、可自检、可完整复现所有功能。任何实施步骤必须以本文档为准。

---

## 一、项目概述

### 1.1 目标
构建一个部署在 **GitHub Pages** 上的静态网站，名为「我的世界物品百科」。

网站展示《我的世界》1.21.11 版本中**所有物品**（包括方块、工具、武器、食物、材料等全部物品类型）的：
- 获取方式与获取路径
- 合成配方（可视化 3×3 网格）
- 烧炼/切石/锻造配方
- 物品图标与配方图片（直接抓取自 Minecraft Wiki CDN）

### 1.2 核心功能
| 功能模块 | 说明 |
|----------|------|
| **搜索** | 顶部常驻搜索栏，支持中文名、英文名、物品 ID 模糊搜索 |
| **浏览模式** | 搜索栏下方分层分类区域：大类 → 小类 → 单个物品 |
| **详情页** | 点击任意物品弹出详情面板：配方可视化 + 获取路径 |
| **图片加载** | 物品图标与配方图片全部来自 Wiki CDN，本地无图片文件 |

### 1.3 部署目标
- 部署平台：**GitHub Pages**（静态托管）
- 无需后端服务器，全部为静态文件（HTML + CSS + JS + JSON）
- 可通过 `https://<username>.github.io/<repo>/` 直接访问

---

## 二、网站功能详细规格

### 2.1 顶部搜索栏（全局固定）

**位置**：页面顶部，始终可见（`position: sticky`）

**交互逻辑**：
1. 用户输入关键词（≥1个字符）时，实时过滤并显示下拉建议列表（最多显示 10 条）
2. 建议列表每项显示：物品图标（16×16）+ 中文名 + 英文名
3. 点击建议项或按 Enter → 打开该物品的详情面板
4. 输入框为空时，下拉列表消失，恢复浏览模式视图
5. 按 Esc 键清空搜索框并收起建议列表

**搜索范围**：`name_zh`（中文名）、`name_en`（英文名）、`id`（物品 ID），三字段模糊匹配

---

### 2.2 浏览模式（分层分类导航）

**结构**：搜索栏正下方，三层递进展示

#### 第一层：大类网格
- 展示所有物品大类（约 10 个），每个大类为一张卡片
- 每张卡片包含：代表性图标（从该大类中取首个物品图标）+ 大类中文名 + 物品数量角标
- 未选中任何大类时，显示全部大类卡片
- 点击大类卡片 → 展开第二层小类

#### 第二层：小类标签页
- 在大类卡片下方（或替换大类区域）展示该大类下的所有小类
- 以横向标签（Tab）形式排列
- 点击某个小类标签 → 在下方展示该小类的物品网格（第三层）
- 顶部显示面包屑导航：`全部 > {大类名} > {小类名}`

#### 第三层：物品网格
- 以网格形式展示该小类下所有物品（每行 6 个，响应式）
- 每个物品格子：图标（32×32）+ 中文名（最多显示 2 行，超出省略）
- 鼠标悬停时显示英文名 tooltip
- 点击物品格子 → 打开详情面板（不跳转页面，以侧边栏或模态框形式展示）

**面包屑导航**（始终显示在浏览区顶部）：
- `全部` → 返回第一层大类网格
- `{大类名}` → 返回该大类的小类列表
- `{小类名}` → 当前页面（不可点击）

---

### 2.3 物品详情面板

**触发方式**：点击任意物品（来自搜索结果或浏览模式）

**展示形式**：右侧滑入侧边栏（桌面端宽度 420px；移动端全屏）

**关闭方式**：点击面板外区域、点击右上角关闭按钮、按 Esc 键

**面板内容结构**（从上到下）：

```
┌─────────────────────────────────────┐
│ [图标 64×64]  物品中文名             │
│               物品英文名             │
│               物品 ID               │
│               [所属大类] [所属小类]  │
├─────────────────────────────────────┤
│ 获取方式                             │
│  • 方式1（如：自然生成）             │
│  • 方式2（如：合成）                 │
│  • 方式3（如：交易）                 │
├─────────────────────────────────────┤
│ 合成配方（如有）                     │
│  ┌───┬───┬───┐                      │
│  │   │   │   │  → [结果图标×数量]   │
│  ├───┼───┼───┤                      │
│  │   │   │   │                      │
│  ├───┼───┼───┤                      │
│  │   │   │   │                      │
│  └───┴───┴───┘                      │
│  配方类型：工作台 / 无序合成         │
├─────────────────────────────────────┤
│ 烧炼/切石/锻造配方（如有）           │
│  [输入图标] → [燃料] → [输出图标]   │
│  经验值：X  烧炼时间：X秒            │
├─────────────────────────────────────┤
│ 自然生成位置（如有）                 │
│  文字描述列表                        │
├─────────────────────────────────────┤
│ 相关物品                             │
│  [图标] [图标] [图标]（可点击）     │
└─────────────────────────────────────┘
```

**URL Hash**：打开详情时更新 URL hash 为 `#item/{item_id}`，支持直接链接分享，刷新后自动重新打开对应详情面板。

---

## 三、UI 设计规范

### 3.1 整体风格
- 风格定位：**简洁、沉稳、专业**，参考现代百科/文档网站风格
- 颜色策略：**不使用高饱和度颜色**，以中性色和低饱和度暖色为主调
- 细节：卡片阴影、圆角、hover 状态变化体现精致感

### 3.2 色彩系统

```css
:root {
  /* 背景色系 */
  --bg-primary:    #f5f4f0;   /* 页面主背景（米白色） */
  --bg-surface:    #ffffff;   /* 卡片/面板背景 */
  --bg-hover:      #eeece6;   /* 悬停背景 */
  --bg-active:     #e5e2d8;   /* 激活/选中背景 */

  /* 文字色系 */
  --text-primary:  #1a1a1a;   /* 主要文字 */
  --text-secondary:#5c5c5c;   /* 次要文字 */
  --text-muted:    #9a9a9a;   /* 弱化文字 */

  /* 强调色（低饱和度） */
  --accent:        #5c7a5c;   /* 绿色系强调（呼应 Minecraft 自然主题） */
  --accent-light:  #e8f0e8;   /* 强调色浅背景 */
  --accent-dark:   #3d5c3d;   /* 强调色深色（hover） */

  /* 边框色 */
  --border:        #dbd8d0;   /* 常规边框 */
  --border-strong: #c0bdb5;   /* 强调边框 */

  /* 功能色（均为低饱和度） */
  --color-crafting:  #6b7fa3; /* 合成配方蓝 */
  --color-smelting:  #a3766b; /* 烧炼配方橙红 */
  --color-natural:   #6b9c6b; /* 自然生成绿 */
  --color-trade:     #9c8c6b; /* 交易黄棕 */
}
```

### 3.3 字体
```css
font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
/* 通过 Google Fonts CDN 引入 Noto Sans SC */
```

### 3.4 组件规范

| 组件 | 规格 |
|------|------|
| 搜索框 | 高度 48px，圆角 24px，边框 1px solid `--border`，聚焦时边框变为 `--accent` |
| 大类卡片 | 宽度自适应，最小 120px，圆角 12px，白色背景，hover 时微上移（translateY -2px）+ 阴影加深 |
| 物品格子 | 80×96px（图标区域 48px，文字区域 48px），圆角 8px，hover 时背景变为 `--bg-hover` |
| 详情侧边栏 | 420px 宽，白色背景，左侧 1px 边框，顶部无圆角，整体 box-shadow |
| 合成格 | 每格 48×48px，边框 1px，背景 `#f0ede6`，内含居中图标 32×32px |
| 标签页 | 高度 36px，圆角 18px，选中时背景 `--accent-light`，文字颜色 `--accent-dark` |

---

## 四、数据结构规格

### 4.1 data.json 主格式

```json
{
  "meta": {
    "version": "1.21.11",
    "generated_at": "2025-xx-xx",
    "total_items": 1234,
    "source": "minecraft.wiki"
  },
  "categories": [
    {
      "id": "building_blocks",
      "name_zh": "建筑方块",
      "name_en": "Building Blocks",
      "icon_item": "stone",
      "subcategories": [
        {
          "id": "stone_materials",
          "name_zh": "石类材料",
          "name_en": "Stone Materials",
          "items": ["stone", "cobblestone", "granite", "..."]
        }
      ]
    }
  ],
  "items": [
    {
      "id": "stone",
      "name_zh": "石头",
      "name_en": "Stone",
      "category": "building_blocks",
      "subcategory": "stone_materials",
      "icon_url": "https://minecraft.wiki/images/Stone.png",
      "incomplete": false,
      "zh_fallback": false,
      "referenced_only": false,
      "source": "wiki",
      "acquisition": {
        "methods": ["自然生成", "精准采集", "烧炼"],
        "natural_generation": ["主世界地下 Y=8 以下", "山地生物群系地表"],
        "drops_from": ["使用精准采集附魔工具挖掘石头方块"],
        "smelting": {
          "input_id": "cobblestone",
          "input_icon": "https://minecraft.wiki/images/Cobblestone.png",
          "fuel": "任意燃料",
          "output_id": "stone",
          "output_icon": "https://minecraft.wiki/images/Stone.png",
          "output_count": 1,
          "experience": 0.1,
          "cook_time_seconds": 10
        },
        "trading": null
      },
      "crafting": [
        {
          "type": "crafting_table",
          "shaped": true,
          "pattern": [
            ["stone", "stone", ""],
            ["stone", "stone", ""],
            ["",      "",      ""]
          ],
          "ingredients": {
            "stone": {
              "id": "stone",
              "name_zh": "石头",
              "icon_url": "https://minecraft.wiki/images/Stone.png"
            }
          },
          "result_id": "stone_slab",
          "result_icon": "https://minecraft.wiki/images/Stone_Slab.png",
          "result_count": 6,
          "recipe_image_url": "https://minecraft.wiki/images/Stone_Slab_recipe.png"
        }
      ],
      "stonecutting": null,
      "smithing": null,
      "related_items": ["cobblestone", "stone_bricks", "stone_slab"]
    }
  ]
}
```

### 4.2 大类划分（预定义）

| 大类 ID | 中文名 | 代表物品 |
|---------|--------|----------|
| `building_blocks` | 建筑方块 | stone |
| `colored_blocks` | 彩色方块 | white_wool |
| `natural_blocks` | 自然方块 | grass_block |
| `functional_blocks` | 功能方块 | crafting_table |
| `redstone` | 红石 | redstone |
| `tools` | 工具 | iron_pickaxe |
| `combat` | 战斗 | iron_sword |
| `food` | 食物 | bread |
| `materials` | 材料 | iron_ingot |
| `miscellaneous` | 杂项 | paper |

---

## 五、数据采集规格（Python 爬虫）

### 5.1 采集目标
- **物品范围**：1.21.11 版本所有物品（方块 + 非方块物品）
- **数据来源**：https://minecraft.wiki（英文 Wiki，数据最完整）
- **中文名补充**：https://zh.minecraft.wiki（仅用于补充中文名称）
- **图标来源**：Wiki CDN（`https://minecraft.wiki/images/` 路径下的图片，直接存储 URL，不下载到本地）

### 5.2 采集字段（每个物品）

| 字段 | 来源 | 必填 | 说明 |
|------|------|------|------|
| `id` | infobox / URL | ✅ | 英文 ID，小写下划线格式 |
| `name_en` | infobox title | ✅ | 英文名 |
| `name_zh` | zh.minecraft.wiki | ✅ | 中文名，缺失则用英文名并设 `zh_fallback: true` |
| `category` + `subcategory` | 分类页 / infobox | ✅ | 对照第四节大类表进行映射 |
| `icon_url` | infobox 图片 | ✅ | Wiki CDN URL |
| `acquisition.methods` | 正文获取方式章节 | ✅ | 方式列表 |
| `acquisition.natural_generation` | 正文 | ❌ | 生成位置文字 |
| `acquisition.smelting` | 烧炼配方模板 | ❌ | 结构化配方 |
| `acquisition.trading` | 交易章节 | ❌ | 交易条件 |
| `crafting[]` | Crafting 模板 | ❌ | 可有多个配方 |
| `stonecutting` | Stonecutting 模板 | ❌ | 切石机配方 |
| `smithing` | Smithing 模板 | ❌ | 锻造台配方 |
| `related_items` | 页面链接 | ❌ | 相关物品 ID |

### 5.3 爬虫技术选型

```
requests==2.31.0          # HTTP 请求（同步，Wiki 不需要异步）
beautifulsoup4==4.12.3    # HTML 解析
lxml==5.1.0               # BS4 解析后端（更快）
tqdm==4.66.2              # 进度条
```

> **依赖严格控制**：requirements.txt 仅含以上 4 个依赖，不额外引入其他库。

### 5.4 爬虫架构

```
scraper/
├── requirements.txt
├── main.py              # 入口：协调采集流程，输出 data.json
├── fetcher.py           # 网络请求封装（重试、缓存、限速）
├── parser.py            # Wiki 页面解析（配方模板、infobox）
├── mapper.py            # 分类映射（Wiki 分类 → 本项目大类/小类）
├── validator.py         # 数据验证与自检
└── cache/               # 页面缓存（{item_id}.html）
    └── .gitignore       # 缓存不提交到 Git
```

### 5.5 爬虫运行流程

```
Step 1: fetcher.py → 获取物品列表
  - 请求 https://minecraft.wiki/w/Java_Edition_1.21.1
  - 提取该版本所有物品链接
  - 输出：item_urls.json（物品 URL 列表）

Step 2: main.py → 逐页采集
  - 遍历 item_urls.json
  - 检查 cache/{item_id}.html 是否存在（断点续传）
  - 不存在则请求并缓存，存在则直接读取
  - 解析后追加到 data_raw.json

Step 3: validator.py → 数据验证
  - 字段完整性检查
  - 中文名覆盖率统计
  - icon_url 格式验证（仅检查格式，不做 HTTP 请求）
  - 输出验证报告 validation_report.json

Step 4: main.py → 输出最终文件
  - 合并 data_raw.json + data_fallback.json（兜底数据）
  - 如果 data.json > 5MB → 按大类拆分为 data_{category}.json
  - 输出最终 data.json（或拆分文件）到 web/data/
```

---

## 六、前端技术规格

### 6.1 技术选型

| 层面 | 技术 | CDN 地址 |
|------|------|----------|
| 框架 | 原生 HTML/CSS/JS（ES6+） | 无 |
| 字体 | Noto Sans SC | `https://fonts.googleapis.com/css2?family=Noto+Sans+SC` |
| 图标 | Minecraft Wiki CDN | 直接使用 `icon_url` 字段中的地址 |
| 数据 | 静态 JSON | `fetch('./data/data.json')` |

> **禁止引入任何 JS 框架**（React/Vue/D3 等），禁止使用构建工具（npm/webpack/vite）。  
> **无网状图需求**：本版本不实现力导向图，使用分层分类浏览模式替代。

### 6.2 文件结构

```
web/
├── index.html              # 唯一 HTML 文件（SPA 单页应用）
├── css/
│   └── style.css           # 全局样式（含所有 CSS 变量）
├── js/
│   ├── app.js              # 应用入口（初始化、路由、全局状态）
│   ├── search.js           # 搜索逻辑（模糊匹配、下拉建议）
│   ├── browser.js          # 浏览模式（大类/小类/物品网格渲染）
│   ├── detail.js           # 详情面板（侧边栏渲染、配方可视化）
│   └── data.js             # 数据加载（fetch + 缓存到内存）
└── data/
    ├── data.json           # 主数据文件（或拆分文件）
    └── data_fallback.json  # 兜底数据（50 个核心物品，手动维护）
```

### 6.3 路由规范

- 路由基于 URL Hash，无需服务器配置
- `#` / `#browser` → 浏览模式首页（大类网格）
- `#browser/{category_id}` → 大类下的小类列表
- `#browser/{category_id}/{subcategory_id}` → 小类下的物品网格
- `#item/{item_id}` → 打开指定物品的详情面板（同时保留浏览模式背景）
- 例：`#browser/building_blocks/stone_materials#item/stone` → 浏览石类材料，同时打开石头的详情

### 6.4 性能规范

| 指标 | 要求 |
|------|------|
| data.json 大小 | ≤ 5MB；超出则拆分，懒加载非当前大类数据 |
| 搜索响应时间 | 输入后 ≤ 100ms 显示结果（本地 JSON 过滤） |
| 图片加载 | 所有 `<img>` 必须有 `onerror` 回退到内联 SVG 占位图 |
| 首屏加载 | index.html + style.css + app.js 总计 ≤ 100KB（不含数据和图片）|

### 6.5 图片容错（必须实现）

```javascript
// 所有图片必须使用此函数生成，禁止直接写 <img src="...">
function createItemIcon(iconUrl, alt, size = 32) {
  const img = document.createElement('img');
  img.src = iconUrl;
  img.alt = alt;
  img.width = size;
  img.height = size;
  img.loading = 'lazy';
  img.onerror = function() {
    this.replaceWith(createPlaceholderIcon(alt, size));
  };
  return img;
}

function createPlaceholderIcon(alt, size) {
  // 生成内联 SVG 占位图（显示物品名首字母）
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', size);
  svg.setAttribute('height', size);
  svg.setAttribute('viewBox', '0 0 32 32');
  svg.innerHTML = `<rect width="32" height="32" rx="4" fill="#dbd8d0"/>
    <text x="16" y="21" text-anchor="middle" font-size="14" fill="#9a9a9a">${alt?.[0] || '?'}</text>`;
  return svg;
}
```

---

## 七、GitHub Pages 部署规格

### 7.1 仓库结构

```
<repo>/                    # 仓库根目录
├── README.md              # 项目说明（含使用方法）
├── scraper/               # 爬虫脚本（不部署）
│   ├── requirements.txt
│   ├── main.py
│   ├── fetcher.py
│   ├── parser.py
│   ├── mapper.py
│   └── validator.py
└── docs/                  # GitHub Pages 源目录（Settings → Pages → /docs）
    ├── index.html
    ├── css/style.css
    ├── js/
    └── data/
        ├── data.json
        └── data_fallback.json
```

> **关键**：GitHub Pages 设置为从 `/docs` 目录发布（无需单独分支）。

### 7.2 部署步骤

1. 在 GitHub 仓库 Settings → Pages → Source 选择 `Deploy from a branch`
2. Branch 选择 `main`，Folder 选择 `/docs`
3. 保存后等待约 1 分钟，网站自动上线

### 7.3 .gitignore 配置

```gitignore
scraper/cache/             # 爬虫页面缓存
scraper/__pycache__/
scraper/*.log
scraper/data_raw.json
scraper/item_urls.json
scraper/validation_report.json
*.pyc
.DS_Store
```

---

## 八、自检与验证规范（CRITICAL）

> **以下所有自检项目必须在每个阶段完成后执行，不得跳过。**

### 8.1 数据自检（validator.py 输出）

运行命令：`python scraper/validator.py docs/data/data.json`

输出示例：
```
=== 数据验证报告 ===
总物品数：1247
  ✅ 满足最低要求（≥ 300）

字段完整性：
  ✅ name_zh 覆盖率：100%（其中 zh_fallback 标记 23 项）
  ✅ name_en 覆盖率：100%
  ✅ category 覆盖率：100%
  ✅ acquisition.methods 覆盖率：97.3%（26 项标记 incomplete）

数据质量：
  ✅ JSON 格式合法
  ✅ 无重复 item ID
  ✅ 版本标记（referenced_only: 14 项）

文件大小：
  ✅ data.json：3.2MB（≤ 5MB）

=== 验证通过 ===
```

**验证失败判定**：以下任意一项失败则整体失败：
- 物品总数 < 300
- `name_zh` 覆盖率 < 95%（允许最多 5% 使用 zh_fallback）
- JSON 格式非法
- 存在重复 item ID

### 8.2 前端自检清单

在浏览器打开 `docs/index.html` 后，按以下步骤逐项验证：

```
[ ] 1. 页面加载
    [ ] 页面无控制台报错
    [ ] 搜索框可见且可输入
    [ ] 大类网格正确渲染（≥ 5 个大类卡片显示）
    [ ] 至少一个大类卡片有正常图标（非占位图）

[ ] 2. 搜索功能
    [ ] 输入"石头"→ 下拉建议出现石头相关物品
    [ ] 输入"stone"→ 下拉建议出现 stone 相关物品
    [ ] 输入不存在的词 → 显示"无搜索结果"提示
    [ ] 按 Esc → 搜索框清空，建议列表消失
    [ ] 点击建议项 → 正确打开对应物品详情面板

[ ] 3. 浏览模式
    [ ] 点击大类"建筑方块"→ 出现小类标签页
    [ ] 面包屑显示"全部 > 建筑方块"
    [ ] 点击"全部"面包屑 → 返回大类网格
    [ ] 点击任一小类标签 → 显示物品网格
    [ ] 物品网格中每个格子图标和名称正常显示

[ ] 4. 详情面板
    [ ] 点击任意物品 → 侧边栏从右侧滑入
    [ ] URL hash 更新为 #item/{id}
    [ ] 面板内物品图标正常显示
    [ ] 合成配方（如有）以 3×3 网格显示
    [ ] 每个配方格内图标正常（有 onerror 回退）
    [ ] 获取方式列表正常显示
    [ ] 点击面板外区域 → 面板关闭
    [ ] 刷新页面后，URL hash 对应的详情面板自动重新打开

[ ] 5. 已知配方验证（对照 Wiki 手动核实）
    [ ] 工作台（crafting_table）：2×2 木板合成，结果为工作台×1
    [ ] 木棍（stick）：2×1 木板合成，结果为木棍×4
    [ ] 石镐（stone_pickaxe）：3 圆石 + 2 木棍，结果为石镐×1

[ ] 6. 图片容错
    [ ] 临时将某个 icon_url 改为无效 URL
    [ ] 确认显示 SVG 占位图（首字母）而非破损图标

[ ] 7. URL 直链
    [ ] 直接访问 index.html#item/stone → 自动打开石头详情
    [ ] 直接访问 index.html#browser/building_blocks → 自动打开建筑方块大类

[ ] 8. 兼容性
    [ ] Chrome 最新版：全部功能正常
    [ ] Edge 最新版：全部功能正常
```

### 8.3 部署后自检

在 GitHub Pages 部署完成后（等待 1-2 分钟），访问 `https://<username>.github.io/<repo>/`：

```
[ ] 网站正常加载（非 404）
[ ] data.json 正常获取（浏览器 Network 面板检查）
[ ] 基本功能（搜索、浏览、详情）在线上环境正常运行
[ ] Wiki CDN 图片可正常加载
```

---

## 九、爬虫安全限制（CRITICAL）

| # | 限制项 | 规则 | 失败处理 |
|---|--------|------|----------|
| 1 | **请求间隔** | 每次请求后 sleep **3~5 秒**（随机），绝不并发 | 超频被限 → 停止 30 分钟后重试 |
| 2 | **User-Agent** | 设置为 `Mozilla/5.0 (compatible; MinecraftWikiResearch/1.0; +https://github.com/<repo>)` | 不得含 bot/scraper 字样 |
| 3 | **Robots.txt** | 启动前读取 `https://minecraft.wiki/robots.txt`，遵守 `Disallow` 规则 | 被禁止的路径不请求 |
| 4 | **缓存优先** | 每页请求前检查 `cache/{item_id}.html`，存在则跳过网络请求 | 中断后重启不重复请求 |
| 5 | **超时重试** | 单页超时 30 秒，失败自动重试最多 3 次，间隔递增（5/10/20秒） | 3 次全失败 → 跳过，写入 error.log |
| 6 | **404 处理** | HTTP 404 → 记录到 skip.log，继续下一个 | 最后人工补全 |
| 7 | **日志** | 所有异常带时间戳写入 scraper.log | 不静默吞掉任何异常 |
| 8 | **版本过滤** | 忽略标记为 "upcoming"、"removed"、"Bedrock Edition only" 的配方 | 带版本条件的配方做版本过滤 |

---

## 十、兜底数据规格（data_fallback.json）

**用途**：在爬虫数据不足时确保网站可用（P0 阶段先行手动维护）。

**覆盖物品**（50 个核心物品，手动整理）：

```
建筑方块：stone, cobblestone, granite, diorite, andesite, sand, gravel,
          oak_planks, oak_log, glass, bricks, stone_bricks

自然方块：grass_block, dirt, oak_leaves, oak_sapling, water_bucket

功能方块：crafting_table, furnace, chest, torch, ladder, door (oak_door),
          bed (white_bed), bookshelf, enchanting_table

工具：wooden_pickaxe, stone_pickaxe, iron_pickaxe, wooden_axe, wooden_shovel

武器：wooden_sword, stone_sword, iron_sword, bow, arrow

食物：bread, apple, cooked_beef, carrot, potato, cooked_chicken

材料：oak_log (wood), coal, iron_ore, iron_ingot, gold_ingot, diamond,
      string, feather, leather, paper

杂项：stick, bowl, book, map, compass
```

每个条目必须包含：`id`、`name_zh`、`name_en`、`category`、`subcategory`、`icon_url`、`acquisition.methods`，以及合成配方（如有）。

`"source": "manual"` 标记所有兜底数据条目。

---

## 十一、实施优先级与完成判定

### 阶段划分

| 阶段 | 内容 | 完成判定 |
|------|------|----------|
| **P0** | 项目骨架 + 兜底数据（50物品）+ 完整前端 | 前端自检清单全部通过（使用兜底数据） |
| **P1** | 爬虫脚本开发与调试 | validator.py 验证通过，物品数 ≥ 300 |
| **P2** | 爬虫运行，生成完整 data.json | 物品数 ≥ 800，数据验证通过 |
| **P3** | 替换兜底数据，全站联调 | 前端自检清单全部通过（使用完整数据） |
| **P4** | 部署到 GitHub Pages | 部署后自检通过 |
| **P5** | 优化（搜索增强、响应式、加载性能） | 可选，按需进行 |

### 整体完成判定标准

下列所有条件必须同时满足，项目才算完成：

```
✅ 1. docs/data/data.json 存在且 JSON 格式合法
✅ 2. 物品总数 ≥ 300（验证命令：python scraper/validator.py docs/data/data.json）
✅ 3. 前端自检清单（第八节 8.2）全部通过
✅ 4. GitHub Pages 部署后自检（第八节 8.3）通过
✅ 5. 已知配方（工作台、木棍、石镐）在详情面板中正确显示
```

---

## 十二、当前状态

- [x] plan.md v1 已创建
- [x] plan.md v2 已更新（功能规格完整化、UI 设计规范化、自检体系建立）
- [ ] P0：项目骨架 + 兜底数据 + 前端实现
- [ ] P1：爬虫脚本开发
- [ ] P2：数据采集
- [ ] P3：数据替换与联调
- [ ] P4：GitHub Pages 部署