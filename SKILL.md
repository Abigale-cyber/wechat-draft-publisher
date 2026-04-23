---
name: wechat-draft-publisher
description: 将公众号文章转为带图的 HTML，上传图片到微信图床，推送到草稿箱。当用户说"发草稿箱"、"配图发布"、"推到公众号"时使用。负责配图、排版、发布，不写不改文章。
---

# WeChat Draft Publisher

## 触发条件

- 用户说"发草稿箱"、"推到公众号"、"配图发布"
- 用户说"帮我看看成文效果"（生成预览）
- 用户说"发布"（只推草稿箱，不直接群发）

**不触发：**
- "写文章" → wechat-article-writer
- "改标题"、"去AI味" → content-polisher
- "审稿" → adversarial-content-review

## 不做什么

- 不写文章、不改文章
- 不做选题、不做 brief
- 不直接群发（只推草稿箱）

## 执行流程

### Step 1: 读取文章

读取用户指定的 article-draft.md 文件，提取：
- 标题、摘要
- 正文 Markdown
- 字数

### Step 2: 配图规划

读取 `references/image-and-layout.md` 中的配图规则（含三维选择系统）。

根据文章类型预设自动匹配维度组合（信息类型 × 渲染风格 × 色调），或用户指定维度。

分析文章结构，确定配图方案：

**封面图（1张）：**
- 根据文章标题和核心观点，生成封面图 prompt
- 尺寸：900x383

**内容图（2-4张）：**
- 文章开头后插第 1 张（氛围图）
- 每 2-3 个章节之间各插 1 张（打断文字墙）
- 为每张图生成描述、类型、风格、色调

### Step 3: 获取图片

调用 `content-image-gen` skill 生图，读取 `../content-image-gen/SKILL.md` 了解用法。

按优先级尝试：

1. **AI 生图**：运行 `~/.agents/skills/writing/content-image-gen/scripts/generate.sh --prompt "{场景描述}" --preset {文章预设} --output {输出路径}`
2. **Unsplash 搜索**：用 WebSearch 搜索 `site:unsplash.com [关键词]`，选合适的图
3. **提示用户提供**：如果以上都不可用，列出每张图的描述和尺寸要求，让用户自备

### Step 4: 检查 API 凭证

读取 `_shared/env-config.md` 中的凭证配置。

按优先级查找微信 API 凭证：
1. CLI 环境变量 / process.env
2. 项目级 `.writing-skills/.env`
3. 用户级 `~/.writing-skills/.env`
4. EXTEND.md 中的凭证字段
5. 都没有 → 告诉用户如何配置，只生成本地预览

### Step 5: 上传图片（有 API 凭证时）

```bash
# 获取 token
# 上传内容图片（uploadimg）→ 获得微信图床 URL
# 上传封面图片（add_material）→ 获得 media_id
```

如果图片还没生成（Step 3 走了提示用户提供），先停下来让用户准备图片。

### Step 6: 转换 HTML

读取 `references/image-and-layout.md` 中的转换规则（含主题色方案）。

读取 `_shared/extend-system.md` 检查是否有自定义排版参数。

将 Markdown + 图片 → 公众号兼容 HTML：
- 所有样式内联（公众号不支持 class）
- 根据文章预设自动选择主题色（default / warm / dark），EXTEND.md 可覆盖
- 字号 15px、行高 2、加粗色随主题、两端对齐
- 图片用 `<figure>` 包裹，插入对应位置
- 遵守 `_shared/wechat-channel-profile.md` 的排版规范

### Step 7: 创建草稿（有 API 凭证时）

调用 `draft/add` API 创建草稿：
- title、content（HTML）、thumb_media_id（封面）
- digest（摘要，64 字以内）
- 返回草稿 media_id

### Step 8: 输出

**始终生成本地预览：** `preview-<选题关键词>.html`
- 可在浏览器直接打开
- 包含所有样式和图片
- 用于发布前确认效果

**有 API 凭证时额外输出：**
- 草稿箱 media_id
- 提示用户到公众号后台草稿箱查看

## Guardrails

- 只推草稿箱，不直接群发
- 图片必须上传到微信图床后才能在文章中显示（外部图片 URL 不行）
- API 凭证缺失时不阻塞，先生成本地预览
- 封面图必须有（草稿 API 要求 thumb_media_id）
- HTML 中所有样式必须内联
- 发布前让用户确认预览效果
