# 发布流程与 API

## 前置条件

发布需要微信公众号的 API 凭证。凭证读取规范见 `_shared/env-config.md`。

**凭证读取顺序（env-config.md 定义）：**
1. CLI 环境变量 / process.env
2. 项目级 `.writing-skills/.env`
3. 用户级 `~/.writing-skills/.env`
4. EXTEND.md 中的凭证字段
5. 以上都没有 → 停下来让用户提供

## API 调用流程

### Step 1: 获取 access_token

```
GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}
```

返回：
```json
{ "access_token": "xxx", "expires_in": 7200 }
```

**注意：** token 有效期 2 小时。如果请求失败，检查 appid/appsecret 是否正确。

### Step 2: 上传内容图片

```
POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={TOKEN}
Content-Type: multipart/form-data
media: @image_file
```

返回：
```json
{ "url": "https://mmbiz.qpic.cn/..." }
```

这个 URL 只能在公众号文章中使用，外部无法访问。

### Step 3: 上传封面图片（永久素材）

```
POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={TOKEN}&type=image
Content-Type: multipart/form-data
media: @cover_image
```

返回：
```json
{ "media_id": "xxx", "url": "https://mmbiz.qpic.cn/..." }
```

封面图要求：
- 推荐尺寸：900 x 383（2.35:1）或 1:1
- 格式：JPG / PNG
- 大小：不超过 2MB

### Step 4: 创建草稿

```
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token={TOKEN}
Content-Type: application/json

{
  "articles": [{
    "title": "文章标题",
    "author": "作者名",
    "digest": "摘要（64字以内）",
    "content": "<p>HTML 正文</p>",
    "content_source_url": "",
    "thumb_media_id": "封面图的 media_id",
    "need_open_comment": 1,
    "only_fans_can_comment": 0
  }]
}
```

返回：
```json
{ "media_id": "草稿 media_id" }
```

草稿创建后，可在公众号后台 → 草稿箱 中看到。

## 错误处理

| 错误码 | 含义 | 处理 |
|--------|------|------|
| 40001 | token 无效或过期 | 重新获取 token |
| 40004 | 不存在的媒体类型 | 检查图片格式 |
| 41001 | 缺少 access_token | 检查凭证配置 |
| 45009 | API 调用次数超限 | 等待后重试 |
| 48001 | API 无权限 | 确认公众号已认证 |

## curl 命令模板

```bash
# 获取 token
TOKEN=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$APPID&secret=$APPSECRET" | jq -r '.access_token')

# 上传内容图
IMG_URL=$(curl -s -F "media=@image.jpg" "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=$TOKEN" | jq -r '.url')

# 上传封面
COVER_ID=$(curl -s -F "media=@cover.jpg" "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=$TOKEN&type=image" | jq -r '.media_id')

# 创建草稿
DRAFT_ID=$(curl -s -X POST "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"articles\":[{\"title\":\"标题\",\"content\":\"HTML内容\",\"thumb_media_id\":\"$COVER_ID\"}]}" \
  | jq -r '.media_id')
```
