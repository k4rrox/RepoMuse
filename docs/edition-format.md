# Edition format

An **edition** is one run's picks. `python3 -m repomuse publish` validates it and merges it into
`data/editions.json`. The page only shows what the edition states; it never infers a license, growth or stack.

A full example lives in [`examples/edition.example.json`](../examples/edition.example.json).

## Edition

| Field | Required | Meaning |
| --- | --- | --- |
| `day` | yes | `YYYY-MM-DD`, the run's date in the configured timezone |
| `updated_at` | yes | ISO time with offset, for example `2026-10-17T09:00:00+08:00` |
| `projects` | yes | picks in editorial order; `[]` is a valid edition |

## Project

| Field | Required | Meaning |
| --- | --- | --- |
| `name`, `repo` | yes | display name and `owner/repo` (unique within a day, case-insensitive) |
| `topic` | yes | one of the topic ids in `repomuse.json` (checked when publishing) |
| `event` | yes | `new`, `update` (major release of an earlier pick) or `demo` (demo for an earlier recommendation) |
| `title`, `summary`, `reason` | yes | what it is for, what it does, why now |
| `fit` | no | why it suits this user, pointing at their profile or feedback |
| `explore` | no | `true` for the one pick per edition outside the profile |
| `verdict` | yes | `try`, `watch` or `observe` |
| `effort` | yes | `low` (try now), `medium` (needs setup), `high` (needs a lab setup) |
| `platforms` | yes | non-empty list, for example `["macOS", "Linux"]` |
| `tags` | no | up to 12 short labels |
| `use_case`, `requirements`, `assessment` | yes | where it fits, what it needs, your judgement and its basis |
| `caution` | no | untested claims and known limits |
| `license` | yes | `{ name, kind, url }`, `kind` is `open-source`, `source-available` or `unverified` |
| `stars` | no | `{ count, observed_at, approximate }`, a snapshot, never a growth figure |
| `heat` | no | `{ label, window, observed_at, total_only }`, growth from a stated source window |
| `tech_stack` | no | see below; shown as "not verified yet" when missing |
| `demo` | no | see below |
| `sources` | yes | 1-20 `{ label, url, observed_at? }`, HTTPS only |

Rules that keep the page honest:

- A missing value stays missing. Never fill a gap with an estimate or with today's number for an old day.
- `stars.count` is a whole number of at least 0. A rounded reading (8.9k) is `8900` with `approximate: true`.
- Without verified growth, leave out `heat`; the card says there is no verified growth data.
- Every link is HTTPS. Every time includes a UTC offset.
- When publishing (not when loading old data): no `*_at` time may be in the future, `day` must have started
  somewhere, at most one pick is `explore: true`, and a `ready` demo needs `demos/<slug>/index.html`.

## Tech stack

```json
{
  "items": [{ "name": "React", "role": "UI components" }, { "name": "TypeScript", "role": "Source" }],
  "sources": [{ "label": "package.json", "url": "https://github.com/owner/repo/blob/main/package.json" }],
  "verified_at": "2026-10-17T09:00:00+08:00",
  "note": "Core stack from the official manifest; not every module was run."
}
```

1-8 items (3-6 is typical): core language, runtime, UI framework, key libraries, data layer. Not the whole
dependency list, optional plugins or target databases. For skill projects say whether it is instructions,
generator scripts or a runtime library. `demo.tech_stack` lists only what the demo itself runs.

## Demo

```json
{
  "status": "ready",
  "path": "/demos/project-slug/",
  "title": "One small experiment",
  "summary": "What you can do once it opens.",
  "tested_at": "2026-10-17T10:30:00+08:00",
  "evidence": "What was actually clicked, and what happened.",
  "limitations": "What was not verified; what is simulated."
}
```

`status` is `ready`, `blocked` or `failed`. Only `ready` has a `path`, and it must be exactly
`/demos/<slug>/`. For `blocked` and `failed`, `evidence` and `limitations` explain why. Attach demos with
`python3 -m repomuse attach-demo owner/repo demo.json`.

## Feedback

The page writes likes and dislikes to `data/feedback.json`:

```json
{ "schema_version": 1, "votes": {
  "owner/repo": { "vote": "like", "at": "2026-10-17T21:04:11+08:00" },
  "owner/other": { "vote": "dislike", "at": "2026-10-17T21:05:02+08:00",
                   "reasons": ["too-heavy", "too-early"], "note": "needs a GPU" }
} }
```

`reasons` is only for a dislike, and each value is one of `off-topic`, `too-heavy`, `already-known`, `too-early`
or `inaccurate` (the run skill says how the agent uses each). `note` holds the user's own words, up to 500 characters.

Read it with `python3 -m repomuse feedback --json`, which joins each vote with the pick it refers to.

## Upgrading from Open Source Radar

`python3 -m repomuse migrate old/daily.json` writes a schema 2 `data/editions.json`. Set `timezone` in
`repomuse.json` to the old file's timezone to keep the same day boundaries.
