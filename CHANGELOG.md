# Changelog

## Unreleased

- Demo library thumbnails sit at the top of their card instead of floating in the middle of tall cards.
- READMEs show the demo library between the picks page and a demo.

## 0.1.0 (2026-10-17)

First public version, grown out of the author's private "Open Source Radar".

- Agent skills: `repomuse-setup`, `repomuse-run`, `repomuse-demo`, routed by `AGENTS.md` / `CLAUDE.md`.
- Personal profile (`profile.md`) and feedback written back to `data/feedback.json` from the page.
- `fit` ("why for you") and `explore` (outside your profile) fields.
- Configurable title, language, timezone, cadence, picks per run and topics in `repomuse.json`.
  English interface; agents translate it into `strings.json` for other languages.
- `publish` merges by repo within a day; `--replace` rewrites the day. `attach-demo`, `feedback`, `seen`.
- Cross-platform `cover` command (headless Chrome, Chromium or Edge; pure-Python PNG crop).
- `migrate` upgrades Open Source Radar v1 data.
- `mode`: `ui` (local page) or `no-ui` (picks in the chat). New `digest`, `vote` and `demo` commands; demos run
  on their own port (page port + 1), and on their own the demo server shows a plain list of demos.
- READMEs in English, Simplified Chinese and Japanese; screenshots in `docs/images/`.
- Publishing rejects unknown fields (with a "did you mean" hint); `check` validates `strings.json` keys and
  `{placeholders}` against the English interface.
- The chat digest converts times without a zone database where it can (UTC) and otherwise keeps the
  recorded offset; `pip install tzdata` enables full conversion on Windows.
- CI on Linux (Python 3.9, 3.11, 3.13), macOS and Windows.
