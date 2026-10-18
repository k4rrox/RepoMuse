# Taste Skill — static source lint experiment

One capability only: run the real Taste Skill source scanner against a tiny example, while four controls change its gradient, resting shadow, purple palette and generic copy. The preview is an illustrative static note-product panel, not an AI-generated application or a notes tool.

## Upstream and licensing

- Repository: https://github.com/Leonxlnx/taste-skill
- Fixed commit: `f624f37a8c650b9cc550253104925efe4c8de246`
- Original scanner: https://github.com/Leonxlnx/taste-skill/blob/f624f37a8c650b9cc550253104925efe4c8de246/skills/taste-skill/scripts/lint.mjs
- Skill instructions: https://github.com/Leonxlnx/taste-skill/blob/f624f37a8c650b9cc550253104925efe4c8de246/skills/taste-skill/SKILL.md
- MIT License, copyright 2026 Leonxlnx; exact upstream license and original files retained in `source/upstream/`.

`scanner.js` is generated from the original `lint.mjs`. `source/build.py` removes the shebang and two Node imports, wraps the entire CLI in a function and supplies local filesystem/path/process/console adapters. The complete rule table and scan loop remain unchanged. No hand-picked findings or hardcoded scan results are used. JSON output is captured from the CLI; its exit becomes a local sentinel. Input is one generated source string instead of files on disk.

## Reproduce

From this demo directory:

```sh
python3 source/build.py
node source/verify.mjs
```

No packages or build dependencies are needed. Node 22+ is recommended. The verification compares all 16 control combinations to the **unmodified** upstream Node CLI; file-path fields are normalized solely for comparison. `scanner.js` is the only derived upstream runtime file. Serve this directory with the existing radar server; no new service is needed.

## What to try

1. Original example has 3 FAIL / 3 WARN.
2. Remove gradient and resting shadow: 1 FAIL / 3 WARN remains, with exact rule IDs and source line numbers.
3. Apply all adjustments: 0 FAIL / 0 WARN; reset restores the original.

The page also exposes the exact generated source it scans. It makes no requests, uses no external fonts or libraries, no local storage, and runs under the radar server's sandbox `allow-scripts` without same-origin permission.

## Limits

- This is a source-lint experiment, not a whole Taste Skill design run, model-generated design, visual quality score, DOM inspection, responsive screenshot inspection or proof of improved aesthetics.
- The rules encode this author's preferences, including blanket bans on gradients, purple and static shadows. Heuristic rules can have false positives and do not cover all CSS syntax. The full skill itself says a clean lint report is insufficient.
- Corrected copy and the preview are authored sample content. No real product claims or upstream benchmark results are inferred.
- The upstream shadow regex can flag a spaced `box-shadow: none` declaration. When removing a shadow, this sample removes the declaration from scanned source instead of altering upstream behavior.
- Preview button is explicitly a static sample and performs no action.

## 2026-10-16 update

- Added a "scan real code" editor: the same `scanner.js` checks any input, and clicking a finding selects its line.
- `presets.js` has three presets: a typical AI landing page (15 hits), an excerpt of this page's `web/app.css` / `web/app.js` before the redesign (9 FAIL / 5 WARN; UI labels translated), and the matching styles after it (0 / 0).
- Verified: all three preset counts match the original CLI; typed edits rescan live; the card still goes 3/3 → 0/0; no horizontal overflow at 1360px / 390px; no console errors.
