# Feishu Input

## Supported Sources

- `/docx/<token>` links
- `/wiki/<token>` links that resolve to `docx`

The first version does not support `sheet`, `bitable`, `slides`, or generic Drive file links.

## Resolution Rules

### `docx`

- Extract the path token and use it directly as the target document token.
- Fetch content with:

```bash
lark-cli docs +fetch --as user --doc "<docx-url-or-token>" --format json
```

### `wiki`

- Extract the wiki token from the URL.
- Resolve the underlying node:

```bash
lark-cli wiki spaces get_node --as user --params '{"token":"<wiki_token>"}' --format json
```

- Continue only when:
  - `obj_type == "docx"`
  - `obj_token` is present

Then fetch the real document content with:

```bash
lark-cli docs +fetch --as user --doc "<obj_token>" --format json
```

## Image Reuse Strategy

The workflow should prefer reusing document images before generating new ones.

### Download

`docs +fetch` returns media placeholders like:

```html
<image token="imgcnxxxxxxxx" width="900" height="600" align="center"/>
```

Download each image with:

```bash
lark-cli docs +media-download --as user --token "<image_token>" --output "<local_path>" --overwrite
```

### Re-upload

- Upload reusable content images to the WeChat `media/uploadimg` endpoint
- Upload the selected cover image to the WeChat `material/add_material` endpoint

## Failure Policy

### Hard failures

- malformed Feishu URL
- unsupported source type
- `wiki` that resolves to a non-`docx` object
- permission denied while fetching the document
- missing WeChat credentials
- no usable cover image

### Soft failures

- individual image download failure
- individual image upload failure
- unsupported rich-text fragments that can be flattened into plain paragraphs

Soft failures should be carried into the result `warnings` while the main draft flow continues.

## Default Execution Contract

```bash
python3 scripts/push_feishu_doc_to_wechat.py "<feishu_doc_url>"
```

This command should:

- read the Feishu document
- reuse images when possible
- render a local preview HTML file
- push directly to the WeChat draft box by default
