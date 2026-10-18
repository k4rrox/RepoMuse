import copy
import shutil
import tempfile
from pathlib import Path

from repomuse.config import ROOT, Paths

PROJECT = {
    "name": "Test", "repo": "example/test", "topic": "ai", "event": "new",
    "title": "A test project", "summary": "What it does", "reason": "Why now", "use_case": "Where it fits",
    "requirements": "What it needs", "assessment": "Judgement", "verdict": "watch", "effort": "low",
    "platforms": ["Web"],
    "license": {"name": "MIT", "kind": "open-source", "url": "https://github.com/example/test"},
    "sources": [{"label": "Repository", "url": "https://github.com/example/test"}],
}
DEMO = {"status": "ready", "path": "/demos/tiny-ui/", "title": "Interactive demo",
        "summary": "Switch themes locally", "tested_at": "2026-10-16T09:00:00-07:00",
        "evidence": "Clicked the theme button; the background changed", "limitations": "No server API verified"}
STACK = {
    "items": [{"name": "React", "role": "UI"}],
    "sources": [{"label": "package.json", "url": "https://github.com/example/test/blob/main/package.json"}],
    "verified_at": "2026-10-16T03:00:00-07:00",
    "note": "Only verified parts.",
}


def project(**changes):
    return dict(copy.deepcopy(PROJECT), **changes)


def edition(day="2026-10-14", projects=None, updated_at=None):
    return {"day": day, "updated_at": updated_at or f"{day}T13:00:00-07:00",
            "projects": [project()] if projects is None else projects}


class Checkout:
    """A throwaway repomuse checkout with the real examples and web assets."""

    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "examples", self.root / "examples")
        shutil.copytree(ROOT / "web", self.root / "web")
        self.paths = Paths(self.root)

    def cleanup(self):
        self.temp.cleanup()
