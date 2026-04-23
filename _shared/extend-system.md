# EXTEND 定制系统

所有 writing skills 支持通过 EXTEND.md 文件自定义配置，不改源码。

## 加载优先级（高优先级覆盖低优先级）

1. **项目级** `<cwd>/.writing-skills/<skill-name>/EXTEND.md`
2. **用户级** `~/.writing-skills/<skill-name>/EXTEND.md`
3. **skill 源文件** `~/.agents/skills/writing/<skill-name>/` 及 `_shared/` 中的默认值

## 可定制项

### 排版参数（覆盖 wechat-channel-profile.md）

```yaml
排版:
  字号: 15                    # 默认 15
  字体颜色: "#333"            # 默认 #333
  加粗颜色: "#4a90d9"         # 默认蓝色
  行高: 2                     # 默认 2
  段间距: 15px                # 默认 15px
  对齐: justify               # 默认两端对齐
```

### 主题色（覆盖 image-and-layout.md 的 HTML 转换）

```yaml
主题:
  加粗色: "#4a90d9"
  标题装饰色: "#4a90d9"
  引用边框色: "#4a90d9"
```

### 品牌信息（用于封面图和发布）

```yaml
品牌:
  作者名: string
  公众号名称: string
  默认作者简介: string
```

### 凭证（覆盖 env-config.md）

```yaml
凭证:
  ARK_API_KEY: string
  WECHAT_APP_ID: string
  WECHAT_APP_SECRET: string
```

### 文章类型预设扩展（覆盖 framework-selection.md）

可追加自定义预设，会合并到内置预设列表中：

```yaml
自定义预设:
  - 名称: string
    框架: 故事类|观点类|热点类|清单类|教学类
    语调: string
    配图风格: string
    结尾模板: string
    排版参数: {}
```

## 使用方式

每个 skill 在执行时，先检查 EXTEND.md 是否存在，存在则加载并覆盖默认值。

### 创建项目级定制

```bash
mkdir -p .writing-skills/wechat-article-writer
# 编辑 .writing-skills/wechat-article-writer/EXTEND.md
```

### 创建用户级定制

```bash
mkdir -p ~/.writing-skills/wechat-draft-publisher
# 编辑 ~/.writing-skills/wechat-draft-publisher/EXTEND.md
```

### 示例：换品牌色

创建 `.writing-skills/wechat-draft-publisher/EXTEND.md`：

```yaml
主题:
  加粗色: "#e07c3e"
  标题装饰色: "#e07c3e"
  引用边框色: "#e07c3e"

品牌:
  作者名: "我的名字"
  公众号名称: "我的公众号"
```
