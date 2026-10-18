# Contributing

Thanks for helping. RepoMuse stays small on purpose, so a few ground rules:

- **No new runtime dependencies.** Python standard library and plain browser JavaScript only. No build step.
  Optional tooling (for example a screenshot helper) must degrade gracefully when it is missing.
- **Python 3.9+.** No `match`, no `X | Y` type unions, no `tomllib`.
- **The data contract is the product.** Changes to `repomuse/schema.py` need tests and an update to
  `docs/edition-format.md`. Never make the validator accept guessed or unsourced values.
- **Skills are code too.** If you change what the agent should do, edit the skill in `skills/` and keep
  `AGENTS.md` in sync.
- **Interface copy lives in `STRINGS` in `web/js/strings.js`.** Add new keys there in English; agents translate
  them into a user's `strings.json`. Keys the chat digest shares must stay identical in `repomuse/digest.py`.
- **Front-end modules have one job each, and dependencies only point down:**

  | Layer | Modules | Rule |
  | --- | --- | --- |
  | logic | `strings.js`, `state.js`, `format.js` | no DOM; tested directly in Node |
  | I/O | `api.js`, `storage.js` | talk to the server or the browser, nothing else |
  | widgets | `dom.js`, `parts.js`, `demos.js`, `reasons.js`, `feedback.js`, `cards.js` | build elements from data; never read the URL |
  | page | `render.js`, `main.js` | the only modules that draw the whole page or wire events |

  A widget that needs to redraw gets a `rerender` callback instead of importing `render.js`.
- **Page style.** `node demos/taste-skill/source/upstream/lint.mjs web` must report 0 FAIL.

Before opening a pull request:

```bash
python3 -B -m unittest discover -s tests -v
for f in web/js/*.js; do node --check "$f"; done
python3 -B -m repomuse check
```

Please do not commit your own `profile.md`, `repomuse.json`, `strings.json`, `data/` or demos.
