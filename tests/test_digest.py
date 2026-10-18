import copy
import unittest

from repomuse.config import DEFAULTS, ROOT, validate_config
from repomuse.digest import DEFAULT_STRINGS, pick_edition, render
from repomuse.interface import page_strings

from helpers import DEMO, edition, project

CONFIG = dict(copy.deepcopy(DEFAULTS), timezone="Asia/Shanghai")


def app_strings():
    return page_strings(ROOT)


class DigestTests(unittest.TestCase):
    def test_shared_labels_match_the_page(self):
        page = app_strings()
        self.assertGreater(len(page), 50)
        for key, value in DEFAULT_STRINGS.items():
            if not key.startswith("digest."):
                with self.subTest(key=key):
                    self.assertEqual(page.get(key), value)

    def test_a_pick_carries_fit_reason_facts_and_demo_command(self):
        pick = project(name="Tiny UI", repo="owner/tiny-ui", fit="You asked for small UI kits.", explore=True,
                       stars={"count": 12345, "observed_at": "2026-10-17T01:30:00Z", "approximate": True},
                       demo=dict(DEMO))
        text = render(edition("2026-10-17", [pick]), CONFIG)
        self.assertIn("## RepoMuse · 2026-10-17 · 1 pick", text)
        self.assertIn("### 1. [Tiny UI](https://github.com/owner/tiny-ui) · Watch closely", text)
        self.assertIn("**Why for you** You asked for small UI kits.", text)
        self.assertIn("**Why now** Why now", text)
        self.assertIn("~12,345 stars (2026-10-17 09:30) · MIT · Effort: Low, try it right away · Outside your profile", text)
        self.assertIn("Try it: `python3 -m repomuse demo tiny-ui`", text)
        self.assertIn("1 useful, 3 not for me", text)

    def test_unfinished_demo_shows_its_reason_and_missing_stars_say_so(self):
        demo = dict(DEMO, status="blocked", evidence="Needs a GPU.")
        del demo["path"]
        text = render(edition("2026-10-17", [project(demo=demo), project(repo="a/two")]), CONFIG)
        self.assertIn("**Demo not ready** Needs a GPU.", text)
        self.assertIn("Stars not recorded", text)
        self.assertIn("· 2 picks", text)
        self.assertNotIn("repomuse demo", text)

    def test_empty_and_sample_editions(self):
        empty = render(edition("2026-10-17", []), CONFIG)
        self.assertIn("Nothing in this edition was worth picking.", empty)
        self.assertNotIn("not for me", empty)
        sample = render(edition("2026-10-17"), CONFIG, sample=True)
        self.assertIn("_Sample picks: These ship with RepoMuse", sample)
        self.assertNotIn("not for me", sample)

    def test_agent_translations_apply_and_missing_keys_fall_back(self):
        text = render(edition("2026-10-17", [project(fit="适合你")]), CONFIG,
                      {"fit": "为什么推给你", "digest.picks.one": "1 个推荐"})
        self.assertIn("**为什么推给你** 适合你", text)
        self.assertIn("· 1 个推荐", text)
        self.assertIn("**Why now**", text)

    def test_pick_edition(self):
        data = {"editions": [edition("2026-10-15"), edition("2026-10-17"), edition("2026-10-16")]}
        self.assertEqual(pick_edition(data)["day"], "2026-10-17")
        self.assertEqual(pick_edition(data, "2026-10-15")["day"], "2026-10-15")
        for bad in ({"editions": []}, data):
            with self.assertRaises(ValueError):
                pick_edition(bad, "2026-01-01")

    def test_translation_problems_catch_typos_and_lost_placeholders(self):
        from repomuse.interface import english_strings, translation_problems
        english = english_strings(ROOT)
        self.assertIn("digest.reply", english)
        self.assertEqual(translation_problems({"verdict.try": "值得试用", "shown": "显示 {n} / {total}"}, english), [])
        problems = translation_problems({"verdcit.try": "x", "shown": "显示 {n}", "stars.title": "{time}"}, english)
        self.assertEqual(len(problems), 2)
        self.assertIn("did you mean 'verdict.try'", problems[1] + problems[0])
        self.assertTrue(any("{n}, {total}" in problem for problem in problems))

    def test_mode_is_ui_or_no_ui(self):
        for mode in ("ui", "no-ui"):
            validate_config(dict(copy.deepcopy(DEFAULTS), mode=mode))
        with self.assertRaises(ValueError):
            validate_config(dict(copy.deepcopy(DEFAULTS), mode="cli"))


if __name__ == "__main__":
    unittest.main()
