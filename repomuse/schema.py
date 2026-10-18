"""The data contract shared by the server, the publisher and the agent skills.

The page only shows what an edition states. Facts carry their own observation time; missing values stay
missing instead of being filled with guesses, and nothing is published unless the whole file validates.
"""
import datetime as dt
import difflib
import re
from urllib.parse import urlsplit

from .config import SLUG

SCHEMA_VERSION = 2
DEMO_PATH = re.compile(r"/demos/[a-z0-9]+(?:-[a-z0-9]+)*/")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
EVENTS = {"new", "update", "demo"}
VERDICTS = {"try", "watch", "observe"}
EFFORTS = {"low", "medium", "high"}
LICENSE_KINDS = {"open-source", "source-available", "unverified"}
DEMO_STATES = {"ready", "blocked", "failed"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label, limit=4000):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= limit,
            f"{label} must be non-empty text of at most {limit} characters")


def https_url(value, label):
    text(value, label, 2000)
    parsed = urlsplit(value)
    require(parsed.scheme == "https" and bool(parsed.hostname) and
            not parsed.username and not parsed.password and
            not any(char.isspace() or ord(char) < 32 for char in value),
            f"{label} must be a valid HTTPS link")


def timestamp(value, label):
    text(value, label, 80)
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{label} must be an ISO time with a timezone offset") from exc
    require(parsed.tzinfo is not None and "T" in value, f"{label} must include a time and a timezone offset")


def repo_name(value, label):
    require(isinstance(value, str) and REPO.fullmatch(value) and
            all(part not in {".", ".."} for part in value.split("/")), f"{label} must look like owner/repo")


def sources(items, label, limit=20):
    require(isinstance(items, list) and 1 <= len(items) <= limit, f"{label} needs 1-{limit} entries")
    for source in items:
        require(isinstance(source, dict), f"{label} entries must be objects")
        text(source.get("label"), f"{label}.label", 200)
        https_url(source.get("url"), f"{label}.url")
        if source.get("observed_at") is not None:
            timestamp(source["observed_at"], f"{label}.observed_at")


def validate_tech_stack(stack, label):
    if stack is None:
        return
    require(isinstance(stack, dict), f"{label} must be an object")
    items = stack.get("items")
    require(isinstance(items, list) and 1 <= len(items) <= 8, f"{label}.items needs 1-8 core technologies")
    names = set()
    for item in items:
        require(isinstance(item, dict), f"{label}.items entries must be objects")
        text(item.get("name"), f"{label}.name", 100)
        text(item.get("role"), f"{label}.role", 150)
        name = item["name"].strip().casefold()
        require(name not in names, f"{label} lists {item['name']} twice")
        names.add(name)
    timestamp(stack.get("verified_at"), f"{label}.verified_at")
    if stack.get("note") is not None:
        text(stack["note"], f"{label}.note", 1000)
    sources(stack.get("sources"), f"{label}.sources", 8)


def validate_demo(demo, label):
    require(isinstance(demo, dict), f"{label} must be an object")
    require(demo.get("status") in DEMO_STATES, f"{label}.status must be ready, blocked or failed")
    for field in ("title", "summary", "evidence", "limitations"):
        text(demo.get(field), f"{label}.{field}")
    timestamp(demo.get("tested_at"), f"{label}.tested_at")
    validate_tech_stack(demo.get("tech_stack"), f"{label}.tech_stack")
    path = demo.get("path")
    require((demo["status"] != "ready" and path is None) or
            (demo["status"] == "ready" and isinstance(path, str) and DEMO_PATH.fullmatch(path)),
            f"{label}.path is only for ready demos and must be /demos/<slug>/")
    return demo


def validate_project(project, label, topics=None):
    require(isinstance(project, dict), f"{label} must be an object")
    for field in ("name", "title", "summary", "reason", "use_case", "requirements", "assessment"):
        text(project.get(field), f"{label}.{field}")
    repo_name(project.get("repo"), f"{label}.repo")
    topic = project.get("topic")
    require(isinstance(topic, str) and SLUG.fullmatch(topic), f"{label}.topic must be a topic id")
    if topics is not None:
        require(topic in topics, f"{label}.topic '{topic}' is not in repomuse.json topics")
    require(project.get("event") in EVENTS, f"{label}.event must be new, update or demo")
    require(project.get("verdict") in VERDICTS, f"{label}.verdict must be try, watch or observe")
    require(project.get("effort") in EFFORTS, f"{label}.effort must be low, medium or high")
    for field in ("platforms", "tags"):
        values = project.get(field, [])
        require(isinstance(values, list) and len(values) <= 12 and (field != "platforms" or bool(values)),
                f"{label}.{field} must be a list of text")
        for value in values:
            text(value, f"{label}.{field}", 100)
    for field in ("caution", "fit"):
        if project.get(field) is not None:
            text(project[field], f"{label}.{field}")
    require(isinstance(project.get("explore", False), bool), f"{label}.explore must be true or false")
    validate_tech_stack(project.get("tech_stack"), f"{label}.tech_stack")
    if project.get("demo") is not None:
        validate_demo(project["demo"], f"{label}.demo")
    license_info = project.get("license")
    require(isinstance(license_info, dict), f"{label}.license is required")
    text(license_info.get("name"), f"{label}.license.name", 150)
    require(license_info.get("kind") in LICENSE_KINDS, f"{label}.license.kind is not valid")
    https_url(license_info.get("url"), f"{label}.license.url")
    sources(project.get("sources"), f"{label}.sources")
    stars = project.get("stars")
    if stars is not None:
        require(isinstance(stars, dict), f"{label}.stars must be an object")
        require(type(stars.get("count")) is int and stars["count"] >= 0, f"{label}.stars.count must be a whole number")
        timestamp(stars.get("observed_at"), f"{label}.stars.observed_at")
        require(isinstance(stars.get("approximate", False), bool), f"{label}.stars.approximate must be true or false")
    heat = project.get("heat")
    if heat is not None:
        require(isinstance(heat, dict), f"{label}.heat must be an object")
        text(heat.get("label"), f"{label}.heat.label", 200)
        text(heat.get("window"), f"{label}.heat.window", 300)
        timestamp(heat.get("observed_at"), f"{label}.heat.observed_at")
        require(isinstance(heat.get("total_only"), bool), f"{label}.heat.total_only must be true or false")
    return project


def validate_edition(edition, topics=None):
    """`topics` is checked only for new publications, so renaming a topic never breaks old editions."""
    require(isinstance(edition, dict), "an edition must be an object")
    day = edition.get("day")
    require(isinstance(day, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", day), "day must be YYYY-MM-DD")
    try:
        dt.date.fromisoformat(day)
    except ValueError as exc:
        raise ValueError(f"day {day} is not a real date") from exc
    timestamp(edition.get("updated_at"), "updated_at")
    projects = edition.get("projects")
    require(isinstance(projects, list) and len(projects) <= 100, "projects must be a list of at most 100")
    seen = set()
    for index, project in enumerate(projects):
        validate_project(project, f"projects[{index}]", topics)
        require(project["repo"].lower() not in seen, f"{project['repo']} appears twice in {day}")
        seen.add(project["repo"].lower())
    return edition


TIME_FIELDS = {"updated_at", "observed_at", "verified_at", "tested_at"}
CLOCK_SKEW = dt.timedelta(minutes=10)


def not_in_future(value, label, now=None):
    """Observation times are when something was read; a time after now was guessed, not observed."""
    now = now or dt.datetime.now(dt.timezone.utc)
    if isinstance(value, dict):
        for key, item in value.items():
            if key in TIME_FIELDS and isinstance(item, str):
                when = dt.datetime.fromisoformat(item.replace("Z", "+00:00"))
                require(when <= now + CLOCK_SKEW, f"{label}.{key} {item} is in the future; use the time you read it")
            else:
                not_in_future(item, f"{label}.{key}", now)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            not_in_future(item, f"{label}[{index}]", now)


# Every field the page or the agent understands. A typo such as "fitt" would otherwise be stored and silently ignored.
SOURCE_FIELDS = {"label", "url", "observed_at"}
STACK_FIELDS = {"items", "note", "sources", "verified_at"}
DEMO_FIELDS = {"status", "path", "title", "summary", "tested_at", "evidence", "limitations", "tech_stack"}
PROJECT_FIELDS = {
    "name", "repo", "topic", "event", "tags", "title", "summary", "reason", "fit", "explore", "verdict", "effort",
    "platforms", "use_case", "requirements", "assessment", "caution", "license", "stars", "heat", "tech_stack", "demo",
    "sources",
}
NESTED_FIELDS = {"license": {"name", "kind", "url"}, "stars": {"count", "observed_at", "approximate"},
                 "heat": {"label", "window", "observed_at", "total_only"}}


def known_fields(value, allowed, label):
    unknown = sorted(set(value) - allowed)
    for key in unknown:
        close = difflib.get_close_matches(key, allowed, n=1)
        require(False, f"{label}.{key} is not a known field" + (f"; did you mean {close[0]}?" if close else ""))


def check_stack_fields(stack, label):
    if not isinstance(stack, dict):
        return
    known_fields(stack, STACK_FIELDS, label)
    for index, item in enumerate(stack.get("items") or []):
        known_fields(item, {"name", "role"}, f"{label}.items[{index}]")
    for index, source in enumerate(stack.get("sources") or []):
        known_fields(source, SOURCE_FIELDS, f"{label}.sources[{index}]")


def check_demo_fields(demo, label):
    known_fields(demo, DEMO_FIELDS, label)
    check_stack_fields(demo.get("tech_stack"), f"{label}.tech_stack")


def check_fields(edition):
    known_fields(edition, {"day", "updated_at", "projects"}, "edition")
    for index, project in enumerate(edition["projects"]):
        label = f"projects[{index}]"
        known_fields(project, PROJECT_FIELDS, label)
        for key, allowed in NESTED_FIELDS.items():
            if isinstance(project.get(key), dict):
                known_fields(project[key], allowed, f"{label}.{key}")
        for position, source in enumerate(project.get("sources") or []):
            known_fields(source, SOURCE_FIELDS, f"{label}.sources[{position}]")
        check_stack_fields(project.get("tech_stack"), f"{label}.tech_stack")
        if isinstance(project.get("demo"), dict):
            check_demo_fields(project["demo"], f"{label}.demo")


def validate_publication(edition, now=None):
    """Extra rules for a new publication only, so stored editions never stop loading as time passes."""
    now = now or dt.datetime.now(dt.timezone.utc)
    latest_day = (now + dt.timedelta(hours=14)).date()  # UTC+14 is the earliest calendar on Earth
    require(dt.date.fromisoformat(edition["day"]) <= latest_day, f"day {edition['day']} has not started anywhere yet")
    not_in_future(edition, "edition", now)
    check_fields(edition)
    explore = [project["repo"] for project in edition["projects"] if project.get("explore")]
    require(len(explore) <= 1, f"at most one pick per edition may be explore: true, got {', '.join(explore)}")
    return edition


def validate_data(data):
    require(isinstance(data, dict), "editions data must be an object")
    require(data.get("schema_version") == SCHEMA_VERSION,
            f"schema_version must be {SCHEMA_VERSION}; run `python3 -m repomuse migrate` for older files")
    require(isinstance(data.get("sample"), bool), "sample must be true or false")
    editions = data.get("editions")
    require(isinstance(editions, list) and len(editions) <= 5000, "editions must be a list")
    seen = set()
    for edition in editions:
        validate_edition(edition)
        require(edition["day"] not in seen, f"two editions share the day {edition['day']}")
        seen.add(edition["day"])
    return data


def validate_feedback(data):
    require(isinstance(data, dict) and data.get("schema_version") == 1, "feedback schema_version must be 1")
    votes = data.get("votes")
    require(isinstance(votes, dict) and len(votes) <= 20000, "feedback votes must be an object")
    for repo, entry in votes.items():
        repo_name(repo, "feedback repo")
        require(repo == repo.lower(), "feedback keys are lowercase owner/repo")
        require(isinstance(entry, dict) and entry.get("vote") in {"like", "dislike"}, f"{repo} vote must be like or dislike")
        timestamp(entry.get("at"), f"{repo}.at")
        if entry.get("note") is not None:
            text(entry["note"], f"{repo}.note", 500)
    return data
