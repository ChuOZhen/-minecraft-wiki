# 我的世界物品百科

> Minecraft 1.21.11 全物品百科网站 · 等轴测 3D 交互界面 · Beta Demo

**[在线访问](https://chuozhen.github.io/-minecraft-wiki/)** | 纯静态站点，部署于 GitHub Pages

---

## 项目简介

一站式浏览 Minecraft 1.21.11 版本全部物品的获取方式、合成配方、图标与分类。设计灵感来自 Minecraft 标志性的等轴测方块视角，通过线框正方体上的 3×3 菱形网格导航 9 大物品分类。

### 当前数据规模

| 指标 | 数值 |
|------|------|
| 物品总数 | 1,536 |
| 中文名覆盖率 | 99.9% |
| 合成配方 | 528 个物品（1,619 条配方） |
| 获取方式 | 全部补全（0 个"未知"） |
| 本地图标 | 1,500+ PNG/GIF |

---

## 功能

### 已完成
- **9 大类菱形导航** — 点击立方体顶面菱形进入分类浏览
- **搜索** — 实时模糊匹配中文名、英文名、物品 ID
- **分层浏览** — 大类 → 中类（标签页） → 物品网格
- **详情面板** — 获取方式 + 合成配方 3×3 + 烧炼/切石/锻造 + 自然生成
- **Hash 路由** — 支持直链分享（`#item/stone`）
- **图片容错** — 图标加载失败自动显示 SVG 占位图
- **响应式布局** — 桌面 6 列 / 平板 4 列 / 手机 3 列
- **等轴测 3D 立方体** — SVG 绘制，顶面 3×3 网格，三面光照

### 待开发

- [ ] 物品间关系图谱（JEI 风格原料→产物反向查询）
- [ ] 英文/多语言支持
- [ ] 分类筛选与多选
- [ ] 配方步骤动画
- [ ] PWA 离线缓存
- [ ] 图片懒加载与 WebP 优化
- [ ] 暗色模式
- [ ] 旧版/快照版本切换
- [ ] 数据更新至最新 Minecraft 版本

---

## 技术栈

| 层面 | 技术 |
|------|------|
| 前端 | 原生 HTML/CSS/JS（ES6+），零框架 |
| 字体 | Google Fonts（Noto Sans SC + Press Start 2P） |
| 数据 | 静态 JSON（`data.json`，2.9 MB） |
| 图片 | 本地 PNG/GIF（Wiki CDN 抓取） |
| 部署 | GitHub Pages（`/docs` 目录） |
| 数据采集 | Python 爬虫（BeautifulSoup + requests） |
| AI 分类 | DeepSeek API 批量分类 + 中文翻译 |

---

## 项目结构

```
├── docs/                  # 网站根目录（GitHub Pages 部署源）
│   ├── index.html         # 首页
│   ├── data/
│   │   ├── data.json      # 主数据文件
│   │   └── data_fallback.json
│   ├── images/            # 物品图标
│   ├── css/               # 旧站样式
│   └── js/                # 旧站脚本
├── scripts/               # 开发工具
│   ├── scraper/           # Wiki 爬虫
│   └── *.py               # 数据修复/分类脚本
├── txt/                   # 文档与提示词
│   ├── plan.md            # 项目计划规格 v2.0
│   ├── bug.md             # Bug 清单
│   └── 5月5日.md          # 最新进度报告
└── README.md
```

---

## 本地运行

```bash
cd docs
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

---

## 数据来源

- [minecraft.wiki](https://minecraft.wiki) — 英文 Wiki，物品数据与配方
- [zh.minecraft.wiki](https://zh.minecraft.wiki) — 中文 Wiki，官方译名
- 合成/切石/锻造/烧炼配方通过解析 Wiki `mcui` 组件提取
- 部分物品通过 DeepSeek API 辅助分类与翻译

---

## 版本

- **数据版本**：Minecraft Java Edition 1.21.11
- **站点版本**：Beta v1.0（2026-05-05）
- **状态**：Demo — 核心功能可用，持续迭代中

---

## 致谢

- Minecraft 版权归 Mojang Studios / Microsoft 所有
- 物品数据与图片来自 Minecraft Wiki 社区
- 字体：Google Fonts（Noto Sans SC、Press Start 2P）
