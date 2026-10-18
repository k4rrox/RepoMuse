import copy
import json
import unittest

from repomuse.config import ROOT
from repomuse.schema import validate_data, validate_edition, validate_feedback

from helpers import DEMO, STACK, edition, project


class EditionTests(unittest.TestCase):
    def test_missing_heat_is_valid_but_unsafe_source_is_not(self):
        validate_edition(edition())
        bad = edition(projects=[project(sources=[{"label": "x", "url": "javascript:alert(1)"}])])
        with self.assertRaises(ValueError):
            validate_edition(bad)

    def test_duplicate_repository_naive_time_and_fake_date_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_edition(edition(projects=[project(), project(repo="EXAMPLE/Test")]))
        with self.assertRaises(ValueError):
            validate_edition(edition(updated_at="2026-10-15T13:00:00"))
        with self.assertRaises(ValueError):
            validate_edition(edition(day="2026-02-31"))

    def test_fit_and_explore_are_optional_and_typed(self):
        validate_edition(edition(projects=[project(fit="You asked for local agents.", explore=True)]))
        for changes in ({"fit": " "}, {"explore": "yes"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_edition(edition(projects=[project(**changes)]))

    def test_topics_are_checked_only_when_given(self):
        validate_edition(edition(projects=[project(topic="rust-tools")]))
        validate_edition(edition(projects=[project(topic="rust-tools")]), {"rust-tools"})
        with self.assertRaises(ValueError):
            validate_edition(edition(projects=[project(topic="rust-tools")]), {"agents"})
        with self.assertRaises(ValueError):
            validate_edition(edition(projects=[project(topic="Not A Slug")]))

    def test_stars_snapshot_rules(self):
        validate_edition(edition(projects=[project(stars={"count": 0, "observed_at": "2026-10-14T09:00:00Z"})]))
        for stars in ({"count": -1, "observed_at": "2026-10-14T09:00:00Z"}, {"count": 1.5, "observed_at": "2026-10-14T09:00:00Z"},
                      {"count": True, "observed_at": "2026-10-14T09:00:00Z"}, {"count": 3, "observed_at": "2026-10-14"}):
            with self.subTest(stars=stars), self.assertRaises(ValueError):
                validate_edition(edition(projects=[project(stars=stars)]))


class DemoTests(unittest.TestCase):
    def with_demo(self, demo):
        return edition(projects=[project(demo=demo)])

    def test_optional_demo_and_unfinished_states(self):
        validate_edition(self.with_demo(copy.deepcopy(DEMO)))
        for status in ("blocked", "failed"):
            demo = dict(DEMO, status=status)
            del demo["path"]
            validate_edition(self.with_demo(demo))

    def test_ready_only_accepts_exact_local_slug(self):
        for path in (None, "https://evil.test/", "//evil.test/", "/demos/../", "/demos/a/index.html",
                     "/demos/a/?q=x", "/demos/a/#x", "/demos/a%2fb/", "/demos/.hidden/", "/demos/a_1/"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                validate_edition(self.with_demo(dict(DEMO, path=path)))

    def test_unverified_demo_cannot_provide_link(self):
        for status in ("failed", "blocked", "unknown"):
            with self.subTest(status=status), self.assertRaises(ValueError):
                validate_edition(self.with_demo(dict(DEMO, status=status)))

    def test_missing_evidence_and_naive_timestamp_are_rejected(self):
        for field, value in (("evidence", " "), ("tested_at", "2026-10-16T09:00:00"), ("limitations", "")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_edition(self.with_demo(dict(DEMO, **{field: value})))

    def test_tech_stack_rules(self):
        validate_edition(edition(projects=[project(tech_stack=copy.deepcopy(STACK))]))
        for field, value in (("items", []), ("items", [{"name": "Rust", "role": ""}]),
                             ("items", [{"name": "React", "role": "UI"}, {"name": "react", "role": "again"}]),
                             ("sources", [{"label": "bad", "url": "javascript:alert(1)"}]),
                             ("verified_at", "2026-10-16T03:00:00")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_edition(edition(projects=[project(tech_stack=dict(copy.deepcopy(STACK), **{field: value}))]))


class FileTests(unittest.TestCase):
    def test_bundled_sample_and_example_edition_validate(self):
        data = validate_data(json.loads((ROOT / "examples" / "sample-editions.json").read_text(encoding="utf-8")))
        self.assertTrue(data["sample"])
        validate_edition(json.loads((ROOT / "examples" / "edition.example.json").read_text(encoding="utf-8")))

    def test_feedback_file_rules(self):
        good = {"schema_version": 1, "votes": {"a/b": {"vote": "like", "at": "2026-10-17T09:00:00+08:00"}}}
        validate_feedback(good)
        validate_feedback({"schema_version": 1, "votes": {"a/b": {"vote": "dislike", "at": "2026-10-17T09:00:00+08:00",
                                                                   "reasons": ["too-heavy", "already-known"], "note": "GPU"}}})
        for votes in ({"a/b": {"vote": "like", "at": "2026-10-17T09:00:00+08:00", "reasons": ["too-heavy"]}},
                      {"a/b": {"vote": "dislike", "at": "2026-10-17T09:00:00+08:00", "reasons": ["boring"]}},
                      {"a/b": {"vote": "dislike", "at": "2026-10-17T09:00:00+08:00", "reasons": ["too-early", "too-early"]}},
                      {"a/b": {"vote": "dislike", "at": "2026-10-17T09:00:00+08:00", "reasons": "too-early"}},
                      {"A/b": {"vote": "like", "at": "2026-10-17T09:00:00+08:00"}},
                      {"a/b": {"vote": "love", "at": "2026-10-17T09:00:00+08:00"}},
                      {"a/b": {"vote": "like", "at": "yesterday"}}, {"not-a-repo": {"vote": "like", "at": "2026-10-17T09:00:00Z"}}):
            with self.subTest(votes=votes), self.assertRaises(ValueError):
                validate_feedback({"schema_version": 1, "votes": votes})


if __name__ == "__main__":
    unittest.main()
