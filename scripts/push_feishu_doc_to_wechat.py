#!/usr/bin/env python3
"""Push a Feishu docx/wiki document into the WeChat draft box."""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import re
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any
import subprocess


WECHAT_API = "https://api.weixin.qq.com/cgi-bin"
IMAGE_TAG_RE = re.compile(r'<image\s+token="([^"]+)"[^>]*/?>')
DOCX_RE = re.compile(r"/docx/([^/?#]+)")
WIKI_RE = re.compile(r"/wiki/([^/?#]+)")


class WorkflowError(RuntimeError):
    def __init__(self, stage: str, reason: str, next_step: str | None = None) -> None:
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.next_step = next_step


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read a Feishu docx/wiki link and push it to the WeChat draft box.",
    )
    parser.add_argument("doc_url", help="Feishu docx or wiki URL")
    parser.add_argument(
        "--work-dir",
        default=".tmp/wechat-draft-publisher",
        help="Directory for previews and downloaded media",
    )
    return parser.parse_args()


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_env() -> None:
    cwd_env = Path.cwd() / ".writing-skills" / ".env"
    home_env = Path.home() / ".writing-skills" / ".env"
    load_env_file(cwd_env)
    load_env_file(home_env)


def run_command(cmd: list[str], stage: str, parse_json: bool = False) -> Any:
    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise WorkflowError(
            stage,
            f"Required command not found: {cmd[0]}",
            f"Install {cmd[0]} and retry.",
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise WorkflowError(stage, stderr) from exc

    if not parse_json:
        return completed.stdout

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise WorkflowError(stage, f"Expected JSON output but got: {completed.stdout[:300]}") from exc


def parse_feishu_url(url: str) -> tuple[str, str]:
    docx_match = DOCX_RE.search(url)
    if docx_match:
        return ("docx", docx_match.group(1))
    wiki_match = WIKI_RE.search(url)
    if wiki_match:
        return ("wiki", wiki_match.group(1))
    raise WorkflowError(
        "parse_url",
        f"Unsupported Feishu URL: {url}",
        "Use a /docx/ or /wiki/ link.",
    )


def resolve_docx_target(url: str) -> dict[str, str]:
    kind, token = parse_feishu_url(url)
    if kind == "docx":
        return {"kind": "docx", "token": token, "doc_ref": token, "source_url": url}

    payload = run_command(
        [
            "lark-cli",
            "wiki",
            "spaces",
            "get_node",
            "--as",
            "user",
            "--format",
            "json",
            "--params",
            json.dumps({"token": token}, ensure_ascii=False),
        ],
        stage="resolve_wiki",
        parse_json=True,
    )
    node = payload.get("node") or payload.get("data", {}).get("node") or {}
    obj_type = node.get("obj_type")
    obj_token = node.get("obj_token")
    title = node.get("title", "")
    if obj_type != "docx" or not obj_token:
        raise WorkflowError(
            "resolve_wiki",
            f"Wiki target is unsupported: obj_type={obj_type!r}",
            "Use a wiki link that points to a docx document.",
        )
    return {
        "kind": "wiki",
        "token": token,
        "doc_ref": obj_token,
        "source_url": url,
        "title": title,
    }


def fetch_doc_markdown(doc_ref: str) -> dict[str, Any]:
    payload = run_command(
        [
            "lark-cli",
            "docs",
            "+fetch",
            "--as",
            "user",
            "--doc",
            doc_ref,
            "--format",
            "json",
        ],
        stage="fetch_doc",
        parse_json=True,
    )
    title = payload.get("title") or payload.get("data", {}).get("title")
    markdown = payload.get("markdown") or payload.get("data", {}).get("markdown")
    if not markdown:
        raise WorkflowError(
            "fetch_doc",
            "Fetched document content is empty.",
            "Check that the Feishu document has readable body content.",
        )
    return {"title": title or "Untitled Document", "markdown": markdown, "raw": payload}


def extract_image_tokens(markdown: str) -> list[str]:
    seen: set[str] = set()
    tokens: list[str] = []
    for token in IMAGE_TAG_RE.findall(markdown):
        if token not in seen:
            tokens.append(token)
            seen.add(token)
    return tokens


def slugify(value: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "article"


def locate_downloaded_file(base_path: Path) -> Path:
    if base_path.exists():
        return base_path
    matches = sorted(base_path.parent.glob(base_path.name + "*"))
    if not matches:
        raise WorkflowError(
            "download_media",
            f"Media download did not produce a file for {base_path.name}",
        )
    return matches[0]


def download_feishu_image(token: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "lark-cli",
            "docs",
            "+media-download",
            "--as",
            "user",
            "--token",
            token,
            "--output",
            str(output_path),
            "--overwrite",
        ],
        stage="download_media",
        parse_json=False,
    )
    return locate_downloaded_file(output_path)


def encode_multipart(fields: dict[str, str], files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = f"----codex{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    for field_name, file_path in files:
        mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{field_name}"; '
                    f'filename="{file_path.name}"\r\n'
                ).encode(),
                f"Content-Type: {mime}\r\n\r\n".encode(),
                file_path.read_bytes(),
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode())
    body = b"".join(chunks)
    return body, f"multipart/form-data; boundary={boundary}"


def http_json(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise WorkflowError("http_request", f"HTTP {exc.code}: {body}") from exc


def get_wechat_access_token() -> str:
    app_id = os.environ.get("WECHAT_APP_ID")
    app_secret = os.environ.get("WECHAT_APP_SECRET")
    if not app_id or not app_secret:
        raise WorkflowError(
            "wechat_auth",
            "Missing WECHAT_APP_ID or WECHAT_APP_SECRET.",
            "Set WeChat credentials in the environment or .writing-skills/.env.",
        )
    query = urllib.parse.urlencode(
        {"grant_type": "client_credential", "appid": app_id, "secret": app_secret}
    )
    payload = http_json(f"{WECHAT_API}/token?{query}")
    if payload.get("errcode"):
        raise WorkflowError(
            "wechat_auth",
            f"WeChat access token error: {payload.get('errmsg', payload)}",
        )
    token = payload.get("access_token")
    if not token:
        raise WorkflowError("wechat_auth", "WeChat access token missing from response.")
    return token


def upload_wechat_inline_image(access_token: str, image_path: Path) -> str:
    body, content_type = encode_multipart({}, [("media", image_path)])
    payload = http_json(
        f"{WECHAT_API}/media/uploadimg?access_token={urllib.parse.quote(access_token)}",
        data=body,
        headers={"Content-Type": content_type},
    )
    if payload.get("errcode"):
        raise WorkflowError("upload_inline_image", payload.get("errmsg", str(payload)))
    url = payload.get("url")
    if not url:
        raise WorkflowError("upload_inline_image", "WeChat inline image URL missing.")
    return url


def upload_wechat_cover(access_token: str, image_path: Path) -> str:
    body, content_type = encode_multipart({}, [("media", image_path)])
    payload = http_json(
        f"{WECHAT_API}/material/add_material?access_token={urllib.parse.quote(access_token)}&type=image",
        data=body,
        headers={"Content-Type": content_type},
    )
    if payload.get("errcode"):
        raise WorkflowError("upload_cover", payload.get("errmsg", str(payload)))
    media_id = payload.get("media_id")
    if not media_id:
        raise WorkflowError("upload_cover", "WeChat cover media_id missing.")
    return media_id


def choose_cover_path(downloaded_images: list[Path]) -> Path:
    if not downloaded_images:
        raise WorkflowError(
            "cover_selection",
            "No usable cover image was found in the Feishu document.",
            "Ensure the document contains at least one downloadable image.",
        )
    return downloaded_images[0]


def summarize_markdown(markdown: str) -> str:
    cleaned = IMAGE_TAG_RE.sub("", markdown)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:64]


def convert_inline(text: str, strong_color: str) -> str:
    parts = re.split(r"(\*\*.+?\*\*)", text)
    rendered: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            rendered.append(
                f'<strong style="color:{strong_color};">{html.escape(part[2:-2])}</strong>'
            )
        else:
            rendered.append(html.escape(part))
    return "".join(rendered)


def render_wechat_html(markdown: str, image_map: dict[str, str]) -> str:
    strong_color = "#4a90d9"
    paragraph_style = (
        "font-size:15px;color:#333;line-height:2;margin:0 0 15px;text-align:justify;"
    )
    lines = markdown.splitlines()
    html_parts = [
        '<section style="max-width:640px;margin:0 auto;padding:20px;background:#fff;">'
    ]
    paragraph_buffer: list[str] = []
    list_buffer: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_buffer:
            return
        text = " ".join(item.strip() for item in paragraph_buffer if item.strip())
        html_parts.append(f'<p style="{paragraph_style}">{convert_inline(text, strong_color)}</p>')
        paragraph_buffer.clear()

    def flush_list() -> None:
        if not list_buffer:
            return
        items = "".join(
            f'<li style="margin:0 0 8px;">{convert_inline(item, strong_color)}</li>'
            for item in list_buffer
        )
        html_parts.append(
            '<ul style="font-size:15px;color:#333;line-height:2;margin:0 0 15px 22px;padding:0;">'
            + items
            + "</ul>"
        )
        list_buffer.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        image_match = IMAGE_TAG_RE.fullmatch(stripped)
        if image_match:
            flush_paragraph()
            flush_list()
            image_url = image_map.get(image_match.group(1))
            if image_url:
                html_parts.append(
                    '<figure style="margin:20px 0;text-align:center;">'
                    f'<img src="{html.escape(image_url)}" style="width:100%;border-radius:4px;" />'
                    "</figure>"
                )
            continue

        if stripped == "---":
            flush_paragraph()
            flush_list()
            html_parts.append('<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">')
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            title = convert_inline(stripped[3:], strong_color)
            html_parts.append(
                '<h2 style="font-size:20px;font-weight:bold;color:#333;'
                f'border-left:4px solid {strong_color};padding-left:10px;margin:30px 0 15px;">'
                f"{title}</h2>"
            )
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            title = convert_inline(stripped[2:], strong_color)
            html_parts.append(
                '<h1 style="font-size:22px;font-weight:bold;color:#333;'
                'text-align:center;margin-bottom:25px;">'
                f"{title}</h1>"
            )
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            flush_list()
            quote = convert_inline(stripped.lstrip("> ").strip(), strong_color)
            html_parts.append(
                '<blockquote style="border-left:4px solid #4a90d9;padding:10px 15px;'
                'background:#f8f9fa;margin:15px 0;">'
                f"{quote}</blockquote>"
            )
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_paragraph()
            list_buffer.append(stripped[2:].strip())
            continue

        if stripped.startswith("<") and stripped.endswith(">"):
            # Drop unsupported Feishu XML-like placeholders rather than leaking raw tags.
            flush_paragraph()
            flush_list()
            continue

        flush_list()
        paragraph_buffer.append(stripped)

    flush_paragraph()
    flush_list()
    html_parts.append("</section>")
    return "".join(html_parts)


def write_preview(work_dir: Path, title: str, body_html: str) -> Path:
    slug = slugify(title)
    preview_path = work_dir / f"preview-{slug}.html"
    full_html = textwrap.dedent(
        f"""\
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>预览：{html.escape(title)}</title>
          <style>
            body {{ background: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; }}
            .article {{ max-width: 640px; margin: 0 auto; background: #fff; padding: 20px; min-height: 100vh; }}
          </style>
        </head>
        <body>
          <div class="article">{body_html}</div>
        </body>
        </html>
        """
    )
    preview_path.write_text(full_html, encoding="utf-8")
    return preview_path


def create_wechat_draft(access_token: str, article: dict[str, Any]) -> str:
    payload = {
        "articles": [
            {
                "title": article["title"],
                "author": article.get("author", ""),
                "digest": article["digest"],
                "content": article["content"],
                "content_source_url": article["source_url"],
                "thumb_media_id": article["thumb_media_id"],
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }
        ]
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    response = http_json(
        f"{WECHAT_API}/draft/add?access_token={urllib.parse.quote(access_token)}",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    if response.get("errcode"):
        raise WorkflowError("create_draft", response.get("errmsg", str(response)))
    media_id = response.get("media_id")
    if not media_id:
        raise WorkflowError("create_draft", "WeChat draft media_id missing.")
    return media_id


def main() -> int:
    args = parse_args()
    load_env()
    work_dir = Path(args.work_dir).resolve()
    media_dir = work_dir / "media"
    work_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []

    try:
        target = resolve_docx_target(args.doc_url)
        fetched = fetch_doc_markdown(target["doc_ref"])
        title = fetched["title"] or target.get("title") or "Untitled Document"
        markdown = str(fetched["markdown"])
        image_tokens = extract_image_tokens(markdown)

        access_token = get_wechat_access_token()

        downloaded_images: list[Path] = []
        uploaded_image_urls: dict[str, str] = {}
        for index, token in enumerate(image_tokens):
            base_path = media_dir / f"image-{index:03d}"
            try:
                downloaded = download_feishu_image(token, base_path)
                downloaded_images.append(downloaded)
                uploaded_image_urls[token] = upload_wechat_inline_image(access_token, downloaded)
            except WorkflowError as exc:
                warnings.append(f"image_token={token}: {exc.reason}")

        cover_path = choose_cover_path(downloaded_images)
        thumb_media_id = upload_wechat_cover(access_token, cover_path)
        body_html = render_wechat_html(markdown, uploaded_image_urls)
        preview_path = write_preview(work_dir, title, body_html)
        draft_media_id = create_wechat_draft(
            access_token,
            {
                "title": title,
                "digest": summarize_markdown(markdown),
                "content": body_html,
                "source_url": target["source_url"],
                "thumb_media_id": thumb_media_id,
            },
        )

        result = {
            "ok": True,
            "title": title,
            "source_url": target["source_url"],
            "draft_media_id": draft_media_id,
            "preview_path": str(preview_path),
            "warnings": warnings,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except WorkflowError as exc:
        result = {
            "ok": False,
            "stage": exc.stage,
            "reason": exc.reason,
        }
        if exc.next_step:
            result["next_step"] = exc.next_step
        if warnings:
            result["warnings"] = warnings
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
