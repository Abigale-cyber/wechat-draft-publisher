# 配图与排版规则

## 配图规划

### 封面图

- 数量：1 张
- 尺寸：900 x 383（推荐）或 1:1
- 要求：与文章主题直接相关，文字可读性强
- 来源优先级：AI 生成 > Unsplash > 用户提供

### 内容图

**插位置：**
- 文章开头之后（营造氛围）
- 每 2-3 个章节之间（打破文字墙）
- 总数 2-4 张（不贪多）

**选图原则：**
- 氛围图：呼应上一章节的情绪（如焦虑→行动→希望）
- 插图：具象化某个观点（如"文件夹堆满"→凌乱的桌面图）
- 不用纯装饰图，每张图要有存在的理由

### 图片尺寸规范

| 类型 | 宽度 | 说明 |
|------|------|------|
| 内容图 | 900px | 公众号正文宽度 |
| 封面图 | 900x383px | 头条封面比例 |
| 封面图（次条） | 200x200px | 次条封面 |

## 配图维度选择系统

每张配图通过三个独立维度选择，组合灵活：

### 信息类型（Type）— 图要表达什么

| 类型 | 说明 | 适用场景 |
|------|------|---------|
| `scene` | 氛围渲染，不传达具体信息 | 故事开头、情绪转折处 |
| `framework` | 概念关系图，展示结构 | 方法论、理论框架 |
| `flowchart` | 流程步骤可视化 | 教程、工作流 |
| `comparison` | 并排对比 | 优劣对比、前后对照 |
| `infographic` | 数据/指标可视化 | 技术文章、数据分析 |

### 渲染风格（Style）— 图长什么样

| 风格 | 说明 | 适用场景 |
|------|------|---------|
| `notion` | 极简手绘线画 | 知识分享、SaaS |
| `elegant` | 精致、专业 | 商业、思想领导力 |
| `warm` | 友好、亲切 | 个人成长、生活方式 |
| `blueprint` | 技术蓝图、等距 3D | 架构、系统设计 |
| `watercolor` | 柔和水彩、自然温暖 | 生活方式、旅行 |
| `editorial` | 杂志风格信息图 | 科技解说、新闻 |

### 色调（Palette）— 配色方案

| 色调 | 说明 | 适用场景 |
|------|------|---------|
| `default` | 蓝色系（#4a90d9 主色） | 通用、技术 |
| `warm` | 暖色系（橙、赭、金） | 品牌、生活方式 |
| `macaron` | 马卡龙柔和色 | 教育、知识分享 |
| `mono` | 黑白灰 | 专业、极简 |

### 预设组合

根据文章类型预设自动选择维度组合：

| 文章预设 | 信息类型 | 渲染风格 | 色调 |
|---------|---------|---------|------|
| `deep-insight` | framework / infographic | blueprint | default |
| `story-time` | scene | watercolor | warm |
| `hot-take` | comparison / infographic | editorial | default |
| `how-to` | flowchart | notion | default |
| `quick-list` | infographic | elegant | macaron |

## 图片来源

### 优先级 1：AI 生成

读取 `_shared/env-config.md` 获取 ARK_API_KEY，使用豆包 Seedream 生图。

**prompt 模板（按维度组合）：**
```
[Style] [Type] illustration of [场景描述], [Palette] color scheme, clean and modern style, suitable for WeChat article
```

**维度到 prompt 的映射：**

| 维度值 | prompt 关键词 |
|--------|-------------|
| notion | minimalist hand-drawn line art |
| elegant | refined sophisticated illustration |
| warm | friendly approachable illustration |
| blueprint | technical schematic isometric 3D blueprint |
| watercolor | soft watercolor painting natural warmth |
| editorial | magazine-style infographic |

### 优先级 2：Unsplash 搜索

用 WebSearch 搜索 Unsplash：
```
site:unsplash.com [关键词]
```

选择标准：
- 横构图优先（适合公众号）
- 色调与文章氛围一致
- 简洁，不要太杂

### 优先级 3：用户自备

如果以上都不可用，告诉用户需要提供图片，列出每张图的：
- 位置（在哪个章节之后）
- 建议内容（什么样的图）
- 建议尺寸

## Markdown → HTML 转换规则

公众号 HTML 要求内联样式，不支持 class。

### 主题色方案

读取 `_shared/extend-system.md` 检查是否有自定义主题。无自定义时使用以下内置方案：

| 主题 | 加粗色 | 标题装饰色 | 引用边框色 | 适用文章类型 |
|------|--------|-----------|-----------|------------|
| `default` | `#4a90d9` | `#4a90d9` | `#4a90d9` | 通用、deep-insight、how-to |
| `warm` | `#e07c3e` | `#e07c3e` | `#e07c3e` | story-time |
| `dark` | `#333333` | `#555555` | `#666666` | hot-take（严肃评论） |

根据文章预设自动选择主题色。用户可覆盖。

### 基础转换（以 default 主题为例）

| Markdown | HTML |
|----------|------|
| `## 标题` | `<h2 style="font-size:20px;font-weight:bold;color:#333;border-left:4px solid {标题装饰色};padding-left:10px;margin:30px 0 15px;">标题</h2>` |
| `**加粗**` | `<strong style="color:{加粗色};">加粗</strong>` |
| 段落 | `<p style="font-size:15px;color:#333;line-height:2;margin:0 0 15px;text-align:justify;">内容</p>` |
| `---` | `<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">` |
| `> 引用` | `<blockquote style="border-left:4px solid {引用边框色};padding:10px 15px;background:#f8f9fa;margin:15px 0;">内容</blockquote>` |

### 图片插入

```html
<figure style="margin:20px 0;text-align:center;">
  <img src="{微信图床URL}" style="width:100%;border-radius:4px;" />
</figure>
```

### 整体结构

```html
<section style="max-width:640px;margin:0 auto;padding:20px;">

  <h1 style="font-size:22px;font-weight:bold;color:#333;text-align:center;margin-bottom:5px;">
    标题
  </h1>
  <p style="font-size:13px;color:#999;text-align:center;margin-bottom:25px;">
    摘要
  </p>

  <!-- 正文内容 -->

</section>
```

### 排版参数（对齐 wechat-channel-profile.md，支持 EXTEND.md 覆盖）

| 项目 | 默认值 | EXTEND 可覆盖 |
|------|--------|-------------|
| 正文字号 | 15px | 字号 |
| 标题字号 | 20px (h2) / 22px (h1) | — |
| 正文字色 | #333 | 字体颜色 |
| 加粗字色 | #4a90d9（随主题变） | 加粗颜色 |
| 行高 | 2（约30px） | 行高 |
| 段间距 | 15px | 段间距 |
| 两端对齐 | text-align: justify | 对齐 |

## 本地预览文件

生成一份独立 HTML 文件，包含所有样式和图片，可在浏览器直接打开。用于发布前预览效果。

文件名：`preview-<选题关键词>.html`

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>预览：{标题}</title>
  <style>
    body { background: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; }
    .article { max-width: 640px; margin: 0 auto; background: #fff; padding: 20px; min-height: 100vh; }
  </style>
</head>
<body>
  <div class="article">
    {HTML 内容}
  </div>
</body>
</html>
```
