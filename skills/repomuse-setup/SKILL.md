---
name: repomuse-setup
description: Set up RepoMuse for this user - find or clone the checkout, interview them briefly, write profile.md and repomuse.json, start the local page, and optionally schedule recurring runs. Use when the user installs RepoMuse, says "set up RepoMuse", or no profile.md exists yet.
---

# Set up RepoMuse

Goal: in under ten minutes the user has a profile, a running local page, and (if they want) a recurring run.
Keep the conversation short. One message of questions, then do the work.

## 1. Find the checkout

- If the current directory contains `repomuse/__main__.py`, use it.
- Otherwise, if `$REPOMUSE_DIR` or `~/repomuse` contains it, use that.
- Otherwise ask where to put it (default `~/repomuse`) and, with the user's OK, clone the repository the user installed from.

All commands below run from the checkout root. Requires Python 3.9+ (`python3 --version`); nothing to install.

## 2. Create the files

```sh
python3 -m repomuse init
```

This copies `examples/repomuse.example.json` to `repomuse.json` and `examples/profile.example.md` to `profile.md`.
Both are gitignored: they belong to the user, not to the repository.

## 3. Interview (one message, at most seven questions)

Ask, with a suggested default for each, so the user can answer "defaults are fine":

1. What should I watch for you? (areas, kinds of tools, problems they are working on)
2. Your main languages and stack?
3. Anything you want to see less of?
4. How often and how many? (for example "every weekday morning, up to 3")
5. Language and timezone for the picks? Detect defaults from the system: the IANA zone from
   `readlink /etc/localtime` (the part after `zoneinfo/`) or `timedatectl show -p Timezone --value`, and the
   language from `$LANG`. `date +%Z` gives an abbreviation such as PDT, which is not a valid `timezone`.
6. May I build small demos on my own for picks that are easy to show? (yes / ask me first / no)
7. Where do you want the picks: a local page you browse, or right here in the chat? (page / chat)

## 4. Write what you heard

- `profile.md`: rewrite each section in the user's own words. Keep their phrasing; do not pad it.
  Add a `## Demos` section recording answer 6. Leave `## What the agent has noticed` empty.
- `repomuse.json`:
  - `mode`: `ui` for the local page, `no-ui` for picks delivered in the chat (answer 7). Both keep the
    same data, and the user can switch at any time.
  - `language`: a tag such as `en`, `zh-CN` or `pt-BR`. Picks are written in it and dates follow it.
  - `timezone`: an IANA name such as `Asia/Shanghai`.
  - `cadence`: a plain description, for example `weekdays at 08:30`.
  - `picks_per_run`: `{ "min": 0, "max": N }`. Zero is always allowed: an empty edition is better than a padded one.
  - `topics`: the default is a single `{ "id": "ai", "label": "AI" }`. Replace it with 3-10 entries that match
    the interests, each `{ "id": "kebab-case", "label": "Shown name" }`, with labels in the user's language.
    Older editions keep their topic ids; the page still shows them under their raw id.
- If `language` is not English, translate the page interface: read the `STRINGS` object at the top of
  `web/js/strings.js` and write `strings.json` in the checkout root with the same keys and translated values.
  Keep every `{placeholder}` exactly as it is. Untranslated keys fall back to English, and the file is gitignored.
  Re-check it after updating RepoMuse, since new keys may have been added.
- Run `python3 -m repomuse check` and fix anything it reports.

## 5. Start the page (`ui` mode)

In `no-ui` mode skip this section: nothing needs to keep running. Picks arrive in the chat, and a demo
is opened on demand with `python3 -m repomuse demo <slug>`.

Start `./run.sh` in the background (port from `repomuse.json`, default 53265) and give the user
`http://127.0.0.1:<port>/`. Demos are served on the next port (`<port + 1>`, or `demo_port` in `repomuse.json`),
so both must be free. If the port is taken, change `port` in `repomuse.json` rather than passing a port to
`run.sh`, so `cover` and later runs find the same server. If a RepoMuse server for this checkout is already
listening there, reuse it: it reads the files on every request. Until the first edition is published the page shows clearly labelled sample picks.

## 6. First run and schedule

- Offer to do the first run now with the `repomuse-run` skill.
- If the user wants recurring runs, schedule the `repomuse-run` skill at their cadence using the scheduler
  your environment provides (for example scheduled tasks in Claude Code or Codex automations, or a system
  cron/launchd job that starts your agent non-interactively in the checkout). Confirm the exact schedule
  with the user before creating it, and tell them how to remove it.

## Boundaries

- Do not commit `profile.md`, `repomuse.json`, `data/` or user demos; they are gitignored on purpose.
- Do not read credentials or tokens. GitHub's public pages and API need none for this.
