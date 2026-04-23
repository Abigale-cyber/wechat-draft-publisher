# wechat-draft-publisher

一个用于微信公众号草稿发布的独立 skill 仓库。

它负责：

- 读取 `article-draft.md`
- 读取飞书 `docx/wiki` 文档链接
- 规划封面图和内容配图
- 生成公众号兼容 HTML
- 本地输出预览文件
- 在具备微信 API 凭证时推送到公众号草稿箱

## 仓库结构

```text
.
├── SKILL.md
├── README.md
├── _shared
│   ├── env-config.md
│   ├── extend-system.md
│   └── wechat-channel-profile.md
├── docs
│   └── superpowers
│       ├── plans
│       └── specs
├── scripts
│   └── push_feishu_doc_to_wechat.py
└── references
    ├── feishu-input.md
    ├── image-and-layout.md
    └── publish-pipeline.md
```

## 依赖说明

- 飞书文档读取依赖 `lark-cli`
- 图片生成流程默认会调用外部 `content-image-gen` skill
- 发布公众号草稿需要 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
- AI 生图需要 `ARK_API_KEY`

详细配置见 [_shared/env-config.md](_shared/env-config.md)。

## Feishu To WeChat

支持把飞书 `docx/wiki` 链接直接推到微信草稿箱。

```bash
python3 scripts/push_feishu_doc_to_wechat.py "https://example.feishu.cn/docx/xxxx"
```

默认行为：

- 直接推微信草稿箱
- 同时生成本地预览 HTML
- 优先复用飞书原图并重新上传到微信图床
- 仅支持 `docx/wiki`
- 没有可用封面图时会直接失败

## 说明

这个仓库当前主要发布的是 skill 定义和执行规范文档，适合作为：

- 独立分享的 skill 仓库
- 公众号发布流程规范仓库
- 后续继续补充脚本实现的基础仓库
