---
name: wechat-draft-publisher
description: |
  将文章推送到微信公众号草稿箱。支持两种模式：
  1. 读取飞书文档链接，推送到草稿箱
  2. 从本地 Markdown 文件推送到草稿箱
  当用户说"发草稿箱"、"推到公众号"、"把这个飞书文档发到微信草稿箱"时触发。
version: 2.0.0
tags:
  - wechat
  - publishing
  - feishu
user-invocable: true
metadata:
  openclaw:
    emoji: "\U0001F4DD"
---

# WeChat Draft Publisher

## 触发条件

- 用户发飞书 docx/wiki 链接并说"推到公众号"、"发草稿箱"、"帮我推送"
- 用户说"把这篇文章发到草稿箱"
- 用户说"配置公众号"（首次配置凭证）

**不触发：**
- "写文章" → wechat-article-writer
- "改标题" → content-polisher

---

## 流程 A：配置公众号凭证（首次使用时）

当用户说"配置公众号"或"设置公众号"时执行。

### 步骤 1：向用户索要凭证

对用户说："请提供你的微信公众号 AppID 和 AppSecret，格式如下：
AppID：wxXXXXX
AppSecret：XXXXXXXXXX

可以在 微信公众平台 → 开发 → 基本配置 中获取。"

### 步骤 2：写入凭证文件

收到凭证后，用 write 工具写入以下两个文件：

**文件 1：config.json**
路径：`{baseDir}/config.json`
内容：
```json
{
  "wechat": {
    "appid": "用户提供的AppID",
    "appsecret": "用户提供的AppSecret"
  }
}
```

**文件 2：.env 文件**
路径：`{baseDir}/../.writing-skills/.env`
内容：
```
WECHAT_APP_ID=用户提供的AppID
WECHAT_APP_SECRET=用户提供的AppSecret
```

### 步骤 3：验证配置

运行以下命令验证：
```bash
python3 {baseDir}/scripts/publish.py --help
```

如果成功，告诉用户："配置完成！现在可以推送到草稿箱了。"

---

## 流程 B：飞书文档 → 微信草稿箱

当用户提供飞书 docx/wiki 链接并要求推送到草稿箱时执行。

### 步骤 1：读取飞书文档

使用 feishu_doc_read 工具读取用户提供的飞书文档链接。

如果是 wiki 链接（包含 /wiki/），先用 feishu_doc_read 读取，获取实际 docx 内容。

### 步骤 2：转换为正确的 Markdown 格式

飞书返回的内容可能是纯文本，缺少 Markdown 标记。你必须在保存文件前，将内容转为正确的 Markdown 格式：

1. **文章标题**：用第一行有意义的文字，前面加 `# ` 作为一级标题（只保留一个）
2. **章节标题**：如 "01 xxx"、"模块一 xxx" 等段落，前面加 `## ` 变成二级标题
3. **列表项**：以 "一次性看懂"、"把思维" 等开头的并列短句，前面加 `- ` 变成列表
4. **表格**：转为 Markdown 表格格式（`| 列1 | 列2 |`）
5. **金句/引用**：以 "金句："开头的段落，前面加 `> ` 变成引用
6. **删除重复的标题行**（飞书有时会重复标题）

### 步骤 3：保存为本地 Markdown 文件

用 write 工具将转换后的 Markdown 内容写入 `/tmp/article-to-publish.md`。

### 步骤 3：运行发布脚本

**重要：必须用以下精确命令格式，不要用 cd && 复合命令。**

纯文字模式（无配图，最稳定）：
```bash
python3 {baseDir}/scripts/publish.py --article /tmp/article-to-publish.md --no-images
```

### 步骤 4：报告结果

**如果成功**（输出包含 "草稿创建成功"）：
告诉用户："文章已成功推送到微信公众号草稿箱！请在公众号后台查看。"

**如果失败**（输出包含错误信息）：
如实告诉用户失败的错误信息，不要编造成功。

---

## 流程 C：本地 Markdown 文件 → 微信草稿箱

当用户提供本地文件路径时执行。

### 步骤 1：确认文件存在

用 read 工具读取用户指定的 Markdown 文件。

### 步骤 2：运行发布脚本

```bash
python3 {baseDir}/scripts/publish.py --article 文件路径 --no-images
```

### 步骤 3：报告结果

同流程 B 步骤 4。

---

## 重要规则

1. **只用 python3 命令**，不要用 cd && python3 复合命令（会被沙箱拦截）
2. **脚本文件名是 publish.py 或 publish.sh**，不是 publisher.py，也不是其他任何名字
3. **失败时如实报告**，不要假装成功
4. **不要读取或展示 config.json 的内容**，只报告"已配置/未配置"
5. **封面图问题**：纯文字模式使用默认封面，如无默认封面会失败。如果因封面图失败，告诉用户需要配置图片。
6. **wiki 链接**需要先解析为 docx 才能读取内容

## 禁止事项（必须遵守）

1. **禁止安装任何其他发布 skill** — 不要用 skillhub install wechat-publisher 或安装任何类似的 skill，本 skill 就是唯一的发布工具
2. **禁止直接调用 wenyan 命令** — wenyan 已内置在 publish.py 中作为排版引擎，不需要你手动调用 wenyan
3. **禁止自己写 Python 脚本调 API** — 不要创建 publish_final.py 等自定义脚本，只用 {baseDir}/scripts/publish.py
4. **禁止手动拼接 HTML 让用户复制粘贴** — 必须通过 publish.py 完成发布，不要提供"手动发布"的替代方案
5. **禁止使用 npm/npx 安装任何发布工具** — 发布只用 publish.py
6. **封面图用默认的纯色占位图** — 不需要生成封面图，不需要用户上传封面图，--no-images 模式自动使用纯色封面
7. 如果 publish.py 执行失败，把完整错误信息报告给用户，不要尝试其他方式
