# 凭证配置规范

所有 writing skills 统一的 API 凭证加载规范。

## 凭证读取优先级（高优先级覆盖低优先级）

1. **CLI 环境变量** — 命令行直接传入（如 `ARK_API_KEY=xxx /baoyu-imagine ...`）
2. **系统环境变量** — `process.env` 中已存在的
3. **项目级 .env** — `<cwd>/.writing-skills/.env`
4. **用户级 .env** — `~/.writing-skills/.env`
5. **EXTEND.md** — 项目级或用户级 EXTEND.md 中的 `凭证:` 字段

## 所需凭证

### 生图（豆包 Seedream）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ARK_API_KEY` | 豆包火山引擎 ARK API 密钥 | — |
| `SEEDREAM_IMAGE_MODEL` | 模型 ID | `doubao-seedream-5-0-260128` |
| `SEEDREAM_BASE_URL` | API 端点 | `https://ark.cn-beijing.volces.com/api/v3` |

### 微信公众号发布

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WECHAT_APP_ID` | 公众号 AppID | — |
| `WECHAT_APP_SECRET` | 公众号 AppSecret | — |

## 配置方法

```bash
# 创建用户级配置
mkdir -p ~/.writing-skills

# 写入 .env
cat > ~/.writing-skills/.env << 'EOF'
ARK_API_KEY=your-ark-api-key
SEEDREAM_IMAGE_MODEL=doubao-seedream-5-0-260128

WECHAT_APP_ID=your-app-id
WECHAT_APP_SECRET=your-app-secret
EOF
```

```bash
# 创建项目级配置（团队共享）
mkdir -p .writing-skills
cat > .writing-skills/.env << 'EOF'
ARK_API_KEY=your-ark-api-key
WECHAT_APP_ID=your-app-id
WECHAT_APP_SECRET=your-app-secret
EOF

# 防止提交密钥
echo ".writing-skills/.env" >> .gitignore
```

## 凭证缺失时的处理

| Skill | 缺少凭证时的行为 |
|-------|----------------|
| wechat-draft-publisher（生图） | 提示用户配置，仅生成本地预览不含图 |
| wechat-draft-publisher（发布） | 提示用户配置，生成本地 HTML 预览不推草稿箱 |
