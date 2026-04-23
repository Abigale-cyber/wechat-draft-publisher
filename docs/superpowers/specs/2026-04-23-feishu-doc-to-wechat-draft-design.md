# Feishu Doc To WeChat Draft Design

Date: 2026-04-23
Repository: `/Users/Abigale/All_project/Career/wechat-draft-publisher`

## Summary

Extend `wechat-draft-publisher` from a document-defined workflow into a skill with a stable execution path for Openclaw. The first supported source is a Feishu document link. The skill should accept `docx` and `wiki` links, resolve the underlying document, reuse document images whenever possible, upload usable images to WeChat, render WeChat-compatible HTML, and push the article into the WeChat Official Account draft box without waiting for manual preview confirmation.

The repository will keep the skill definition as the natural-language entry point and add one fixed execution script so Openclaw can call the workflow reliably.

## Goals

- Accept a Feishu `docx` or `wiki` document URL as the main input.
- Resolve `wiki` links to the underlying `docx` document before processing.
- Read the Feishu document content through `lark-cli` with user identity.
- Reuse Feishu document images when possible by downloading them locally and re-uploading them to WeChat.
- Generate a local preview HTML file even when the default behavior is direct push.
- Push the result to the WeChat draft box by default and return the resulting draft `media_id`.
- Keep the existing skill semantics of "draft only, never direct publish".

## Non-Goals

- Supporting Feishu `sheet`, `slides`, `bitable`, or arbitrary Drive file links in v1.
- Reproducing every Feishu rich-text style exactly inside WeChat HTML.
- Handling batch publishing of multiple Feishu documents in one command.
- Adding direct group-send or post-publish WeChat operations.
- Replacing the existing local Markdown workflow in this iteration.

## Chosen Approach

Use a two-layer design:

- `SKILL.md` remains the conversational interface and defines triggers, input contract, and defaults.
- `scripts/push_feishu_doc_to_wechat.py` becomes the stable execution entry point for Openclaw and other automations.

This is preferred over a documentation-only update because Openclaw needs a concrete command to run, and it is preferred over a multi-input workflow because the first version should stay narrowly focused on the Feishu link path.

## User-Facing Behavior

### Supported inputs

- Feishu `docx` URL
- Feishu `wiki` URL that resolves to a `docx` node

### Default behavior

- Receiving a supported Feishu document link starts processing immediately.
- The workflow does not pause for preview confirmation.
- The workflow still writes a local preview HTML artifact for debugging and verification.
- Successful completion returns the Feishu document title, the WeChat draft `media_id`, and the local preview path.

### Unsupported inputs

- Any Feishu URL that is not `docx` or `wiki`
- `wiki` URLs that resolve to a non-`docx` target

Unsupported inputs fail fast with a clear reason.

## Repository Changes

The repository should be expanded to:

```text
wechat-draft-publisher/
├── SKILL.md
├── README.md
├── .gitignore
├── _shared/
│   ├── env-config.md
│   ├── extend-system.md
│   └── wechat-channel-profile.md
├── references/
│   ├── feishu-input.md
│   ├── image-and-layout.md
│   └── publish-pipeline.md
├── scripts/
│   └── push_feishu_doc_to_wechat.py
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-23-feishu-doc-to-wechat-draft-design.md
```

### File responsibilities

- `SKILL.md`
  - Add Feishu document link triggers.
  - Define the script entry point and default direct-push behavior.
  - Preserve the existing draft-only guardrails.
- `references/feishu-input.md`
  - Define supported Feishu URL types, token resolution rules, image reuse strategy, and failure policy.
- `scripts/push_feishu_doc_to_wechat.py`
  - Execute the workflow from Feishu link to WeChat draft creation.
- `README.md`
  - Document dependencies, setup, and Openclaw invocation examples.
- `_shared/env-config.md`
  - Include Feishu prerequisites such as `lark-cli`, identity choice, and permission expectations.

## End-To-End Flow

The command contract for automation should be:

```bash
python3 scripts/push_feishu_doc_to_wechat.py "<feishu_doc_url>"
```

The script should execute the following stages.

### 1. Parse and validate the Feishu URL

- Detect whether the input is a `docx` URL or a `wiki` URL.
- Extract the token from the path.
- Reject malformed or unsupported URLs immediately.

### 2. Resolve Feishu resource identity

- If the input is `docx`, use the path token as the document token.
- If the input is `wiki`, call the Feishu wiki node lookup to retrieve:
  - `obj_type`
  - `obj_token`
  - `title`
- Only continue when the resolved `obj_type` is `docx`.

### 3. Fetch document content

- Use `lark-cli` with user identity to read the resolved document.
- Extract:
  - title
  - body content
  - image references
  - enough structure to preserve headings, paragraphs, quotes, lists, and separators
- If the active identity lacks access, stop with a permission error rather than guessing or silently downgrading.

### 4. Normalize into an internal article model

Before HTML generation, the script should convert Feishu content into a stable intermediate structure such as:

- `title`
- `summary`
- `blocks`
- `images`
- `source_url`

This keeps the renderer independent from Feishu-specific response formats and makes later extension safer.

### 5. Reuse document images

- Prefer images already embedded in the Feishu document.
- Download each usable image to a local temporary workspace.
- Upload each downloaded image to the WeChat article image endpoint.
- Replace the source reference in the internal article model with the resulting WeChat image URL.

If an individual image cannot be downloaded or uploaded:

- record the failure
- skip that image
- continue processing the rest of the document

### 6. Ensure a usable cover image

- If one of the reused Feishu images can serve as a cover, use it.
- Otherwise invoke the existing cover-generation path or fallback image strategy.
- If no cover image can be produced at all, stop the workflow because WeChat draft creation requires `thumb_media_id`.

### 7. Render WeChat-compatible HTML

- Reuse the repository's existing typography and layout rules.
- Convert normalized content blocks into inline-styled HTML compatible with WeChat articles.
- Insert only images that were successfully re-uploaded to WeChat.
- Write a local preview artifact named `preview-<slug>.html`.

### 8. Create the WeChat draft

- Get an access token.
- Upload the cover image as permanent material to obtain `thumb_media_id`.
- Call `draft/add` with:
  - title
  - digest
  - content
  - thumb_media_id
- Return the resulting draft `media_id`.

## Error Handling Policy

Errors are split into hard failures and soft failures.

### Hard failures

These stop the workflow immediately:

- unsupported or malformed Feishu URL
- `wiki` resolution to a non-`docx` object
- inability to read the Feishu document because of permissions or authentication
- missing `WECHAT_APP_ID` or `WECHAT_APP_SECRET`
- inability to produce any valid cover image
- WeChat draft creation failure

Each hard failure must report the failed stage and a practical next step when one exists.

### Soft failures

These do not stop draft creation by default:

- one or more Feishu images fail to download
- one or more images fail to upload to WeChat
- some Feishu formatting cannot be preserved exactly

Soft failures should be accumulated and included in the final result summary. As long as the main body and a valid cover remain available, the workflow should continue.

## Dependencies And Permissions

### Required dependencies

- `python3`
- `lark-cli`
- network access to Feishu and WeChat APIs

### Required identities and credentials

- Feishu reading should use `lark-cli` with `--as user`
- the user identity must have access to the target document
- WeChat publishing requires:
  - `WECHAT_APP_ID`
  - `WECHAT_APP_SECRET`

### Optional credentials

- `ARK_API_KEY` for generated fallback cover images or fill-in artwork

### Identity rules

- Do not default to bot identity for reading user documents.
- If user identity is missing or unauthorized, fail clearly and ask for proper authorization.

## Output Contract

### Success result

The workflow should return:

- `title`
- `source_url`
- `draft_media_id`
- `preview_path`
- `warnings`

### Failure result

The workflow should return:

- `stage`
- `reason`
- `next_step` when actionable

## Testing Strategy

Validate v1 with four scenario groups.

### 1. Basic success path

- Input a `docx` link
- Document contains a title, body, and multiple images
- Expect successful WeChat draft creation and a returned `media_id`

### 2. Wiki success path

- Input a `wiki` link
- Resolve it to the backing `docx`
- Expect the rest of the workflow to succeed unchanged

### 3. Partial degradation path

- Document is readable but some images fail to download or upload
- Expect the workflow to continue and still create a draft
- Expect warnings identifying skipped images

### 4. Explicit failure path

- permission denied on Feishu read
- missing WeChat credentials
- no usable cover image

Each of these should fail fast with a specific stage and message.

## Acceptance Criteria

The first implementation is accepted when all of the following are true:

- A `docx` or supported `wiki` Feishu URL can be given as input.
- `wiki` URLs resolve correctly to the underlying `docx` token.
- The body content is converted into stable WeChat-compatible HTML.
- Feishu images are reused when possible and re-uploaded to WeChat.
- A valid cover image is always required before draft creation.
- The workflow pushes directly to the WeChat draft box by default.
- A successful run returns the WeChat draft `media_id` and local preview path.
- A failed run reports the failed stage clearly.

## Risks And Mitigations

### Feishu structure variance

Risk:
- Feishu documents may contain blocks or formatting not mapped cleanly to WeChat HTML.

Mitigation:
- Normalize into an internal article model first and support only the required common block types in v1.

### Image transport fragility

Risk:
- Feishu-hosted media retrieval may fail for specific documents or permissions.

Mitigation:
- Treat individual image failures as soft failures.
- Require only one valid cover image to proceed.

### Authentication drift

Risk:
- Openclaw may run in an environment where `lark-cli` auth has expired or the wrong identity is active.

Mitigation:
- Check auth and identity early.
- Return explicit remediation steps rather than attempting silent retries with the wrong identity.

## Implementation Boundary For V1

The first implementation should remain intentionally narrow:

- support only `docx/wiki`
- support direct push to draft box only
- favor document fidelity over aggressive auto-enhancement
- reuse original images first, then fall back only when necessary

This keeps the first version suitable for Openclaw automation without broadening the scope into a general publishing platform.
