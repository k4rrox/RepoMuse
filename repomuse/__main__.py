"""Command line used by people and agents: python3 -m repomuse <command>."""
import argparse
import json
import shutil
import sys
from pathlib import Path

from . import __version__
from .config import Paths, demo_port_for, load_config, load_strings
from .store import attach_demo, load_editions, load_feedback, own_editions, publish, set_vote, write_json


def read_input(name):
    return json.loads(sys.stdin.read() if name == "-" else Path(name).read_text(encoding="utf-8"))


def cmd_serve(args, paths):
    from . import server
    server.run(args.port)


def cmd_init(args, paths):
    created = []
    for source, target in ((paths.examples / "repomuse.example.json", paths.config),
                           (paths.examples / "profile.example.md", paths.profile)):
        if target.exists() and not args.force:
            print(f"kept      {target.name} (already exists)")
            continue
        shutil.copyfile(source, target)
        created.append(target.name)
        print(f"created   {target.name}")
    paths.data.mkdir(exist_ok=True)
    (paths.root / "work").mkdir(exist_ok=True)
    load_config(paths)
    if created:
        print("Next: edit them (or let your agent run the repomuse-setup skill), then publish a first edition.")


def cmd_check(args, paths):
    problems = 0
    for label, action in (("repomuse.json", lambda: load_config(paths)),
                          ("strings.json", lambda: load_strings(paths)),
                          ("editions", lambda: load_editions(paths)),
                          ("feedback", lambda: load_feedback(paths))):
        try:
            action()
            print(f"ok        {label}")
        except (OSError, ValueError, TypeError) as error:
            problems += 1
            print(f"invalid   {label}: {error}")
    print(f"{'ok' if paths.profile.exists() else 'missing':9} profile.md")
    if problems == 0:
        problems += check_translation(paths)
    data = load_editions(paths) if problems == 0 else None
    if data is not None:
        projects = sum(len(row["projects"]) for row in data["editions"])
        print(f"{len(data['editions'])} editions, {projects} picks{' (bundled sample)' if data['sample'] else ''}")
    return 1 if problems else 0


def check_translation(paths):
    """A non-English page needs strings.json; its keys and {placeholders} must match the English interface."""
    from .interface import english_strings, translation_problems
    language = load_config(paths)["language"]
    strings = load_strings(paths)
    if language.split("-")[0].lower() == "en" and not strings:
        return 0
    if not strings:
        print(f"note      strings.json is missing, so the page and digest stay in English (language is {language})")
        return 0
    english = english_strings(paths.root)
    problems = translation_problems(strings, english)
    for problem in problems:
        print(f"invalid   strings.json: {problem}")
    print(f"{len(set(strings) & set(english))}/{len(english):<6} interface strings translated")
    return len(problems)


def cmd_publish(args, paths):
    edition = publish(read_input(args.edition), paths, replace=args.replace, check_only=args.check)
    verb = "Checked" if args.check else "Published"
    mode = "replaced" if args.replace else "merged"
    count = len(edition["projects"])
    print(f"{verb} {edition['day']}: {count} pick{'' if count == 1 else 's'} in that edition ({mode}).")


def cmd_attach_demo(args, paths):
    day = attach_demo(args.repo, read_input(args.demo), paths, check_only=args.check)
    print(f"{'Checked' if args.check else 'Attached'} demo for {args.repo} in the {day} edition.")


def picks_index(paths):
    index = {}
    for edition in reversed(own_editions(paths)):  # oldest first, so the newest pick wins
        for project in edition["projects"]:
            index[project["repo"].lower()] = dict(project, day=edition["day"])
    return index


def cmd_feedback(args, paths):
    votes = load_feedback(paths)["votes"]
    picks = picks_index(paths)
    rows = []
    for repo, entry in sorted(votes.items(), key=lambda item: item[1]["at"], reverse=True):
        project = picks.get(repo, {})
        rows.append({"repo": repo, "vote": entry["vote"], "at": entry["at"], "note": entry.get("note"),
                     "topic": project.get("topic"), "title": project.get("title"), "day": project.get("day"),
                     "tags": project.get("tags", []), "effort": project.get("effort")})
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    if not rows:
        print("No feedback yet.")
    for row in rows:
        print(f"{row['vote']:8} {row['repo']:40} {row['topic'] or '-':12} {row['title'] or ''}"
              + (f"  — {row['note']}" if row["note"] else ""))


def cmd_seen(args, paths):
    rows = [{"repo": project["repo"], "day": project["day"], "topic": project["topic"],
             "demo": (project.get("demo") or {}).get("status")} for project in picks_index(paths).values()]
    rows.sort(key=lambda row: row["day"], reverse=True)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    for row in rows:
        print(f"{row['day']}  {row['repo']:40} {row['topic']:12} {row['demo'] or ''}")


def cmd_migrate(args, paths):
    from .migrate import upgrade
    data, timezone = upgrade(read_input(args.source))
    output = Path(args.output) if args.output else paths.editions
    if output.exists() and not args.force:
        raise ValueError(f"{output} exists; pass --force to overwrite it")
    write_json(output, data)
    print(f"Wrote {output} with {len(data['editions'])} editions.")
    if timezone:
        print(f"The old file used {timezone}; set \"timezone\" in repomuse.json to keep the same day boundaries.")


def cmd_digest(args, paths):
    from .digest import pick_edition, render
    data = load_editions(paths)
    text = render(pick_edition(data, args.day), load_config(paths), load_strings(paths), sample=data["sample"])
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")


def cmd_vote(args, paths):
    if not paths.editions.exists():
        raise ValueError("these are the bundled sample picks; publish your first edition before voting")
    vote = None if args.vote == "clear" else args.vote
    set_vote(args.repo, vote, args.note, paths)
    known = args.repo.lower() in picks_index(paths)
    print(f"{'Cleared' if vote is None else 'Saved'} {args.repo}" + ("" if vote is None else f": {vote}")
          + ("" if known else " (note: this repo is not in any published edition)"))


def cmd_demo(args, paths):
    from . import server
    server.run_demos(args.port, args.slug, open_browser=not args.no_open)


def cmd_cover(args, paths):
    from .cover import capture
    print(f"Wrote {capture(args.slug, demo_port_for(load_config(paths), args.port), paths.demos, args.offset)}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="repomuse", description="Personalized GitHub picks, curated by your agent.")
    parser.add_argument("--version", action="version", version=f"repomuse {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="start the local page (127.0.0.1 only)")
    serve.add_argument("--port", type=int)
    init = commands.add_parser("init", help="create repomuse.json and profile.md from the examples")
    init.add_argument("--force", action="store_true", help="overwrite existing files")
    commands.add_parser("check", help="validate settings, editions and feedback")
    pub = commands.add_parser("publish", help="validate and publish one edition (merged into its day by default)")
    pub.add_argument("edition", help="edition JSON file, or - for stdin")
    pub.add_argument("--check", action="store_true", help="validate only, write nothing")
    pub.add_argument("--replace", action="store_true", help="replace the whole day instead of merging by repo")
    att = commands.add_parser("attach-demo", help="attach a demo record to an already published project")
    att.add_argument("repo", help="owner/repo")
    att.add_argument("demo", help="demo JSON file, or - for stdin")
    att.add_argument("--check", action="store_true")
    fb = commands.add_parser("feedback", help="list likes and dislikes with the picks they refer to")
    fb.add_argument("--json", action="store_true")
    seen = commands.add_parser("seen", help="list every repo already picked, newest first")
    seen.add_argument("--json", action="store_true")
    mig = commands.add_parser("migrate", help="upgrade an Open Source Radar v1 daily.json")
    mig.add_argument("source")
    mig.add_argument("--output")
    mig.add_argument("--force", action="store_true")
    dig = commands.add_parser("digest", help="print an edition as Markdown for the chat (no-UI mode)")
    dig.add_argument("--day", help="YYYY-MM-DD; default: the latest edition")
    dig.add_argument("--out", help="also write the Markdown to this file")
    vote = commands.add_parser("vote", help="record feedback from the chat: like, dislike or clear")
    vote.add_argument("repo", help="owner/repo")
    vote.add_argument("vote", choices=("like", "dislike", "clear"))
    vote.add_argument("--note", help="optional reason, kept with the vote")
    dem = commands.add_parser("demo", help="serve demos only and open one in the browser (no-UI mode)")
    dem.add_argument("slug", nargs="?", help="demo folder name; omit for the list of demos")
    dem.add_argument("--port", type=int, help="the page port; demos use the port after it")
    dem.add_argument("--no-open", action="store_true", help="print the link instead of opening a browser")
    cov = commands.add_parser("cover", help="screenshot demos/<slug>/ into its cover image (./run.sh must be running)")
    cov.add_argument("slug")
    cov.add_argument("--offset", type=int, default=0, help="CSS pixels to skip from the top")
    cov.add_argument("--port", type=int, help="the page port ./run.sh uses; demos are read from the port after it")

    args = parser.parse_args(argv)
    paths = Paths()
    handler = globals()["cmd_" + args.command.replace("-", "_")]
    try:
        return handler(args, paths) or 0
    except (OSError, ValueError, TypeError) as error:
        print(f"repomuse {args.command}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
