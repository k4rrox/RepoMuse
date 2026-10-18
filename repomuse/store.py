"""Reading and atomically writing the two data files. A failed validation never touches what is on disk."""
import datetime as dt
import json
import os
import tempfile
import threading
from pathlib import Path

from .config import Paths, load_config, topic_ids
from .schema import (SCHEMA_VERSION, check_demo_fields, not_in_future, repo_name, require, text, validate_data, validate_demo,
                     validate_edition, validate_feedback, validate_publication)

LOCK = threading.Lock()


def now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(destination, data):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_editions(paths=None):
    """Your editions, or the bundled sample (marked `sample: true`) until the first publication."""
    paths = paths or Paths()
    source = paths.editions if paths.editions.exists() else paths.sample_editions
    if not source.exists():
        return {"schema_version": SCHEMA_VERSION, "sample": False, "editions": []}
    return validate_data(read_json(source))


def own_editions(paths):
    return validate_data(read_json(paths.editions))["editions"] if paths.editions.exists() else []


def save_editions(paths, editions):
    editions = sorted(editions, key=lambda row: row["day"], reverse=True)
    data = validate_data({"schema_version": SCHEMA_VERSION, "sample": False, "editions": editions})
    write_json(paths.editions, data)
    return data


def merge_edition(existing, incoming):
    """Keep what the day already has, replace projects with the same repo in place, append new ones.

    A demo attached with `attach-demo` survives a republish that does not carry its own `demo`.
    """
    projects = list(existing["projects"])
    index = {project["repo"].lower(): position for position, project in enumerate(projects)}
    for project in incoming["projects"]:
        key = project["repo"].lower()
        if key in index:
            previous = projects[index[key]]
            if project.get("demo") is None and previous.get("demo") is not None:
                project = dict(project, demo=previous["demo"])
            projects[index[key]] = project
        else:
            index[key] = len(projects)
            projects.append(project)
    return dict(incoming, projects=projects)


def publish(edition, paths=None, replace=False, check_only=False):
    paths = paths or Paths()
    with LOCK:
        validate_edition(edition, topic_ids(load_config(paths)))
        validate_publication(edition)
        for project in edition["projects"]:
            if project.get("demo") is not None:
                require_demo_files(project["demo"], paths)
        editions = own_editions(paths)
        current = next((row for row in editions if row["day"] == edition["day"]), None)
        result = edition if replace or current is None else merge_edition(current, edition)
        editions = [row for row in editions if row["day"] != edition["day"]] + [result]
        if check_only:
            validate_data({"schema_version": SCHEMA_VERSION, "sample": False, "editions": editions})
            return result
        save_editions(paths, editions)
        return result


def require_demo_files(demo, paths):
    """A ready demo must point at a page that exists in this checkout."""
    if demo.get("status") == "ready":
        page = paths.demos / demo["path"].strip("/").split("/", 1)[1] / "index.html"
        require(page.is_file(), f"demo path {demo['path']} has no index.html in this checkout")


def attach_demo(repo, demo, paths=None, check_only=False):
    """Put a demo on the latest edition that already lists the repo, keeping its day and Stars snapshot."""
    paths = paths or Paths()
    repo_name(repo, "repo")
    validate_demo(demo, "demo")
    check_demo_fields(demo, "demo")
    not_in_future(demo, "demo")
    require_demo_files(demo, paths)
    with LOCK:
        editions = own_editions(paths)
        for edition in editions:  # newest first
            for project in edition["projects"]:
                if project["repo"].lower() == repo.lower():
                    project["demo"] = demo
                    if not check_only:
                        save_editions(paths, editions)
                    return edition["day"]
    raise ValueError(f"{repo} is not in any published edition yet; publish it first")


def load_feedback(paths=None):
    paths = paths or Paths()
    if not paths.feedback.exists():
        return {"schema_version": 1, "votes": {}}
    return validate_feedback(read_json(paths.feedback))


def set_vote(repo, vote, note=None, paths=None):
    paths = paths or Paths()
    repo_name(repo, "repo")
    require(vote in {"like", "dislike", None}, "vote must be like, dislike or null")
    if note is not None:
        text(note, "note", 500)
    with LOCK:
        data = load_feedback(paths)
        key = repo.lower()
        if vote is None:
            data["votes"].pop(key, None)
        else:
            entry = {"vote": vote, "at": now_iso()}
            if note:
                entry["note"] = note
            data["votes"][key] = entry
        write_json(paths.feedback, validate_feedback(data))
        return data
