---
name: repomuse-demo
description: Build, verify and attach a small sandboxed demo for a RepoMuse pick, using the project's real upstream code. Use when a pick's value is easiest to see by trying it, when the user asks for a demo of a picked project, or when repomuse-run hands over a demo candidate.
---

# Build a RepoMuse demo

A demo is one small, complete experiment that shows a single capability of a picked project, running the
project's real code. It is what makes a pick tryable in a minute instead of described.

All commands run from the RepoMuse checkout root. Read `demos` in `repomuse.json` first and stay inside it:

| Setting | Meaning |
| --- | --- |
| `policy` | `auto`: build demos on your own. `ask`: propose the demo and wait for a yes. `off`: build none. |
| `scope` | how big a demo may get (below). Anything beyond it is recorded as `blocked`, with the reason. |
| `allow_installs` | `false`: no package installs or builds; only files that run as they are (plain JS, upstream's prebuilt browser bundle). |
| `max_per_run` | at most this many demos in one edition. |

| `scope` | What fits |
| --- | --- |
| `small` | one capability on one static page: a few controls, upstream code used as is, no bundling. |
| `medium` | several interactions or views; you may install packages inside the demo folder and bundle them (esbuild or upstream's own build). |
| `large` | a fuller scenario such as an editable timeline, several linked views or a generated artifact, with heavier local builds. |

Every scope keeps the limits below: no long-running services, paid APIs, credentials or deployment.
`attach-demo` refuses a demo when `policy` is `off`, when the edition already holds `max_per_run` demos, or when
`allow_installs` is `false` and the folder contains `node_modules`, `package.json` or a lock file.

## 1. Choose

- A pick (or an earlier pick without a demo) whose value is visible: UI, diagrams, video or timeline
  composition, a linter you can watch, an interactive tool.
- Skip anything that needs a large application, long-running services, paid APIs or private credentials to show
  its value. Record it as `blocked` with the reason instead of faking it.
- Check the license allows redistribution of what you will copy. No clear license, no demo.

## 2. Build in one folder only

- Work only inside `demos/<slug>/` (slug: lowercase, digits, hyphens). Never touch other demos, other
  projects, global packages or system settings. Install dependencies locally in that folder only.
- Pin the upstream commit. Keep the upstream LICENSE, a short `README.md` (what it shows, pinned commit,
  how to reproduce, limits) and the minimal source needed to rebuild it.
- Put build inputs under `source/` or `src/`; the server never serves `source`, `src`, `scripts`, `tests` or
  `node_modules`, and only serves `index.html` as HTML.
- Use the real upstream component, library or skill workflow. A look-alike page does not count as verified.
- An npm package with bare imports (`import ... from '@scope/pkg'`) cannot load in the browser as is. Install it
  and a bundler (for example esbuild) under `source/`, bundle your entry file into one local `.js` next to
  `index.html`, and keep the exact versions and build command in `source/` so the README can say how to rebuild.
- Do not read credentials, call new paid services or deploy anything.

## 3. Fit the sandbox

Demos are served from their own port (the page port + 1, for example 53266) with `sandbox allow-scripts
allow-same-origin` and `connect-src 'none'`, so they cannot reach the page, its data or the network:

- Ship a static `index.html` with local JS, CSS and images. No CDNs, no inline `<script>`, no network
  requests, no localStorage/cookies, no forms, no popups.
- Start the page with the shared bar so people can get back:

```html
<link rel="stylesheet" href="../radar-kit/bar.css">
<nav class="radar-bar" aria-label="RepoMuse"><a href="/?view=demos">← All demos</a><span class="radar-bar-name">Project · what it is</span><a class="radar-bar-repo" href="https://github.com/owner/repo">View on GitHub</a></nav>
```

- The first screen says what is good about the project, and the interactive part sits near the top.

## 4. Verify like a reviewer

Open `http://127.0.0.1:<port + 1>/demos/<slug>/` in a browser (the page's "Open demo" link goes there) and:

- Use every key interaction and check the result is what upstream would produce.
- Check a narrow (phone) width, a failure or empty path, and the console (no errors).
- If your browser tool cannot open the demo, drive headless Chrome yourself (`--dump-dom`, `--screenshot`, or a
  small DevTools Protocol script that clicks and reads the result). A screenshot alone is not an interaction.
- Label anything simulated (static data, mocked output) on the page itself. Verifying a UI is not verifying the
  AI, MCP server or backend behind it; say so in `limitations`.

Status is `ready` only if real interactions passed. Otherwise `blocked` (a missing condition) or `failed`
(it did not work), with the concrete reason in `evidence`.

## 5. Cover and attach

- With the page running: `python3 -m repomuse cover <slug> --offset <px>` (needs Chrome, Chromium or Edge;
  `--offset` skips the title so the interactive part fills the thumbnail). Or save your own browser screenshot
  as `demos/<slug>/cover.png`. Without a cover the card shows text only.
- Write the demo record (see `examples/demo.example.json` and `docs/edition-format.md`) to
  `work/demo-<slug>.json`, then:

```sh
python3 -m repomuse attach-demo owner/repo work/demo-<slug>.json --check
python3 -m repomuse attach-demo owner/repo work/demo-<slug>.json
```

This adds the demo to the latest edition that lists the repo, keeping its original day and Stars snapshot.
A `ready` demo is refused unless `demos/<slug>/index.html` exists, and `tested_at` cannot be in the future.
Republishing that edition later keeps the attached demo unless the new pick carries its own `demo`.
Tell the user what they can try and what was not verified, and how to open it:

- `ui` mode: the pick's card now has an "Open demo" button (refresh the page).
- `no-ui` mode: start `python3 -m repomuse demo <slug>` in the background (it serves only the demos and opens
  the browser; add `--no-open` to just print the link), give the user the link, and attach the cover image if
  your environment can show images. Stop that process when the user is done with it.
