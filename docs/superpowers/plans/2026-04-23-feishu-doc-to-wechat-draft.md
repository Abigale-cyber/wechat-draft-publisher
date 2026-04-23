# Feishu Doc To WeChat Draft Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Feishu `docx/wiki` link support to `wechat-draft-publisher` and provide a fixed script entry point that pushes a readable Feishu document into the WeChat draft box.

**Architecture:** Keep `SKILL.md` as the trigger and workflow contract, add one Python execution script under `scripts/`, and document Feishu-specific parsing, permissions, and failure policy under `references/` and `_shared/`. The script uses `lark-cli` to fetch document content and media, then uploads WeChat assets and creates the draft.

**Tech Stack:** Markdown skill docs, Python 3 standard library, `lark-cli`, WeChat Official Account HTTP APIs

---

### Task 1: Add Feishu input documentation

**Files:**
- Create: `/Users/Abigale/All_project/Career/wechat-draft-publisher/references/feishu-input.md`
- Modify: `/Users/Abigale/All_project/Career/wechat-draft-publisher/SKILL.md`
- Modify: `/Users/Abigale/All_project/Career/wechat-draft-publisher/_shared/env-config.md`

- [ ] **Step 1: Document supported Feishu input types**

Write `references/feishu-input.md` covering:

```md
# Feishu Input

- Support `/docx/` URLs directly
- Support `/wiki/` URLs only when they resolve to `docx`
- Use `lark-cli wiki spaces get_node --as user --params '{"token":"..."}'` for wiki resolution
- Use `lark-cli docs +fetch --as user --doc "<url-or-token>" --format json` for content
- Use `lark-cli docs +media-download --as user --token "<media_token>" --output <path> --overwrite` for images
```

- [ ] **Step 2: Update skill triggers and defaults**

Edit `SKILL.md` so the trigger section explicitly includes:

```md
- 用户说“把这个飞书文档发到微信草稿箱”
- 用户给出飞书 `docx/wiki` 链接并说“推到公众号”
```

Also add a short execution block:

```bash
python3 scripts/push_feishu_doc_to_wechat.py "<feishu_doc_url>"
```

- [ ] **Step 3: Update credential and permission notes**

Extend `_shared/env-config.md` with Feishu requirements:

```md
### 飞书文档读取

- 依赖：`lark-cli`
- 身份：优先 `--as user`
- 需要文档读取权限
- wiki 链接需要先解析到真实 `docx` token
```

### Task 2: Add the execution script

**Files:**
- Create: `/Users/Abigale/All_project/Career/wechat-draft-publisher/scripts/push_feishu_doc_to_wechat.py`

- [ ] **Step 1: Create the CLI scaffold**

Start the script with:

```python
def main() -> int:
    parser = argparse.ArgumentParser(...)
    parser.add_argument("doc_url")
    parser.add_argument("--work-dir", default=".tmp/wechat-draft-publisher")
    args = parser.parse_args()
```

- [ ] **Step 2: Implement Feishu URL parsing and wiki resolution**

Add helpers with these signatures:

```python
def parse_feishu_url(url: str) -> tuple[str, str]:
    ...

def resolve_docx_target(url: str) -> dict[str, str]:
    ...
```

`resolve_docx_target()` should:
- accept `docx` directly
- call `lark-cli wiki spaces get_node` for `wiki`
- raise a typed error for unsupported targets

- [ ] **Step 3: Implement document fetch and media extraction**

Add:

```python
def fetch_doc_markdown(doc_ref: str) -> dict[str, object]:
    ...

def extract_image_tokens(markdown: str) -> list[str]:
    ...
```

Fetch content with:

```bash
lark-cli docs +fetch --as user --doc "<doc_ref>" --format json
```

- [ ] **Step 4: Implement media download and WeChat upload**

Add:

```python
def download_feishu_image(token: str, output_path: Path) -> Path:
    ...

def upload_wechat_inline_image(access_token: str, image_path: Path) -> str:
    ...

def upload_wechat_cover(access_token: str, image_path: Path) -> str:
    ...
```

- [ ] **Step 5: Implement minimal Markdown-to-WeChat HTML rendering**

Add a renderer that supports:
- headings
- paragraphs
- blockquotes
- horizontal rules
- unordered lists
- inline bold
- image placeholders

- [ ] **Step 6: Implement draft creation and JSON result output**

Add:

```python
def create_wechat_draft(access_token: str, article: dict[str, object]) -> str:
    ...
```

Return JSON with:

```json
{
  "ok": true,
  "title": "...",
  "draft_media_id": "...",
  "preview_path": "...",
  "warnings": []
}
```

### Task 3: Update repository-facing docs

**Files:**
- Modify: `/Users/Abigale/All_project/Career/wechat-draft-publisher/README.md`

- [ ] **Step 1: Document new workflow**

Add a README section with:

```md
## Feishu -> WeChat

```bash
python3 scripts/push_feishu_doc_to_wechat.py "https://.../docx/..."
```
```

- [ ] **Step 2: Document prerequisites and limits**

State:
- only `docx/wiki`
- direct push by default
- image reuse is best-effort
- cover image is required

### Task 4: Verify script integrity

**Files:**
- Test: `/Users/Abigale/All_project/Career/wechat-draft-publisher/scripts/push_feishu_doc_to_wechat.py`

- [ ] **Step 1: Run syntax verification**

Run:

```bash
python3 -m py_compile scripts/push_feishu_doc_to_wechat.py
```

Expected: no output

- [ ] **Step 2: Run CLI help**

Run:

```bash
python3 scripts/push_feishu_doc_to_wechat.py --help
```

Expected: usage text listing `doc_url`

- [ ] **Step 3: Check git status**

Run:

```bash
git status -sb
```

Expected: only intended files modified or created
