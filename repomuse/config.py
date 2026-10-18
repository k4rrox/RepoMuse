"""Site settings in repomuse.json. Everything personal lives next to the checkout and is gitignored."""
import json
import re
from pathlib import Path

try:
    from zoneinfo import ZoneInfo, available_timezones
except ImportError:  # pragma: no cover - Python < 3.9 is not supported, keep the message clear
    raise SystemExit("RepoMuse needs Python 3.9 or newer.")

ROOT = Path(__file__).resolve().parent.parent
MODES = ("ui", "no-ui")
LANGUAGE = re.compile(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

DEMO_POLICIES = ("auto", "ask", "off")
DEMO_SCOPES = ("small", "medium", "large")
# How far the agent may go when it builds demos. Partial objects in repomuse.json are merged over these.
DEMO_DEFAULTS = {"policy": "ask", "scope": "medium", "allow_installs": True, "max_per_run": 1}

# One broad topic out of the box; setup replaces it with the user's own areas.
DEFAULT_TOPICS = [{"id": "ai", "label": "AI"}]
DEFAULTS = {
    "title": "RepoMuse",
    "language": "en",
    "mode": "ui",
    "timezone": "UTC",
    "cadence": "daily at 09:00",
    "picks_per_run": {"min": 0, "max": 3},
    "port": 53265,
    "topics": DEFAULT_TOPICS,
    "demos": DEMO_DEFAULTS,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Paths:
    """Where one checkout keeps its user files. `root` is patchable in tests."""

    def __init__(self, root=None):
        self.root = Path(root or ROOT)
        self.config = self.root / "repomuse.json"
        self.profile = self.root / "profile.md"
        self.strings = self.root / "strings.json"
        self.data = self.root / "data"
        self.editions = self.data / "editions.json"
        self.feedback = self.data / "feedback.json"
        self.demos = self.root / "demos"
        self.work = self.root / "work"
        self.server = self.work / "server.json"  # the ports the running servers use (see ports.py)
        self.web = self.root / "web"
        self.examples = self.root / "examples"
        self.sample_editions = self.examples / "sample-editions.json"


def valid_timezone(name):
    try:
        ZoneInfo(name)
        return True
    except Exception:
        # Windows without the tzdata package has no zone database; accept well-formed names there.
        return not available_timezones() and bool(re.fullmatch(r"[A-Za-z_]+(?:/[A-Za-z0-9_+-]+){0,2}", name))


def validate_demos(demos):
    require(isinstance(demos, dict), "demos must be an object")
    unknown = sorted(set(demos) - set(DEMO_DEFAULTS))
    require(not unknown, f"demos.{unknown[0] if unknown else ''} is not a setting; use {', '.join(DEMO_DEFAULTS)}")
    require(demos["policy"] in DEMO_POLICIES, "demos.policy must be auto (build on its own), ask (ask first) or off")
    require(demos["scope"] in DEMO_SCOPES, "demos.scope must be small, medium or large")
    require(isinstance(demos["allow_installs"], bool), "demos.allow_installs must be true or false")
    require(type(demos["max_per_run"]) is int and 0 <= demos["max_per_run"] <= 5, "demos.max_per_run must be 0-5")


def validate_config(config):
    require(isinstance(config, dict), "repomuse.json must be an object")
    title = config.get("title")
    require(isinstance(title, str) and 0 < len(title.strip()) <= 80, "title must be 1-80 characters")
    require(isinstance(config.get("language"), str) and LANGUAGE.fullmatch(config["language"]),
            "language must be a language tag such as en, zh-CN or pt-BR")
    require(config.get("mode") in MODES, "mode must be \"ui\" (local page) or \"no-ui\" (picks in the chat)")
    require(isinstance(config.get("timezone"), str) and valid_timezone(config["timezone"]),
            "timezone must be an IANA name such as Asia/Shanghai or America/New_York")
    cadence = config.get("cadence")
    require(isinstance(cadence, str) and 0 < len(cadence.strip()) <= 200, "cadence must be a short description")
    picks = config.get("picks_per_run")
    require(isinstance(picks, dict) and all(type(picks.get(k)) is int for k in ("min", "max")) and
            0 <= picks["min"] <= picks["max"] <= 20, "picks_per_run needs integers 0 <= min <= max <= 20")
    port = config.get("port")
    require(type(port) is int and 1024 <= port <= 65535, "port must be between 1024 and 65535")
    demo = config.get("demo_port")
    require(demo is None or (type(demo) is int and 1024 <= demo <= 65535 and demo != port),
            "demo_port must be a different port between 1024 and 65535 (default: port + 1)")
    validate_demos(config.get("demos"))
    topics = config.get("topics")
    require(isinstance(topics, list) and 1 <= len(topics) <= 24, "topics needs 1-24 entries")
    seen = set()
    for topic in topics:
        require(isinstance(topic, dict) and isinstance(topic.get("id"), str) and SLUG.fullmatch(topic["id"]) and
                len(topic["id"]) <= 40, "each topic needs an id like 'agents' or 'web-dev'")
        require(topic["id"] not in seen, f"duplicate topic id: {topic['id']}")
        seen.add(topic["id"])
        label = topic.get("label")
        require(isinstance(label, str) and 0 < len(label.strip()) <= 60, f"topic {topic['id']} needs a short label")
    return config


def load_config(paths=None):
    """User settings merged over defaults. A missing file is fine: the sample site still runs."""
    paths = paths or Paths()
    config = json.loads(json.dumps(DEFAULTS))
    if paths.config.exists():
        user = json.loads(paths.config.read_text(encoding="utf-8"))
        require(isinstance(user, dict), "repomuse.json must be an object")
        if isinstance(user.get("demos"), dict):
            user = dict(user, demos=dict(DEMO_DEFAULTS, **user["demos"]))
        config.update(user)
    return validate_config(config)


def demo_port_for(config, port=None):
    """Demos get their own origin: the configured demo_port, or the page port + 1. The running ports may differ
    when these are busy; ports.running() has those."""
    port = port or config["port"]
    configured = config.get("demo_port")
    return configured if configured and configured != port else port + 1


def topic_ids(config):
    return {topic["id"] for topic in config["topics"]}


def load_strings(paths=None):
    """Optional interface translation the agent writes for a non-English `language`. Missing keys stay English."""
    paths = paths or Paths()
    if not paths.strings.exists():
        return {}
    strings = json.loads(paths.strings.read_text(encoding="utf-8"))
    require(isinstance(strings, dict) and len(strings) <= 500, "strings.json must be an object of interface strings")
    for key, value in strings.items():
        require(isinstance(key, str) and len(key) <= 80 and isinstance(value, str) and len(value) <= 600,
                f"strings.json entry {key!r} must map a key to text")
    return strings
