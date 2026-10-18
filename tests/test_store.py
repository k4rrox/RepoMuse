import copy
import json
import unittest

from repomuse.config import load_config
from repomuse.store import attach_demo, load_editions, load_feedback, publish, set_vote

from helpers import DEMO, Checkout, edition, project


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self.checkout = Checkout()
        self.paths = self.checkout.paths

    def tearDown(self):
        self.checkout.cleanup()

    def saved(self):
        return json.loads(self.paths.editions.read_text(encoding="utf-8"))


class PublishTests(StoreTestCase):
    def test_sample_is_served_until_the_first_publication_replaces_it(self):
        self.assertTrue(load_editions(self.paths)["sample"])
        publish(edition("2026-10-15", []), self.paths)
        data = load_editions(self.paths)
        self.assertFalse(data["sample"])
        self.assertEqual([row["day"] for row in data["editions"]], ["2026-10-15"])

    def test_same_day_publications_merge_by_repo(self):
        publish(edition("2026-10-15", [project(repo="a/one"), project(repo="a/two")]), self.paths)
        publish(edition("2026-10-15", [project(repo="A/TWO", title="Updated"), project(repo="a/three")],
                        updated_at="2026-10-15T20:00:00-07:00"), self.paths)
        day = self.saved()["editions"][0]
        self.assertEqual([p["repo"] for p in day["projects"]], ["a/one", "A/TWO", "a/three"])
        self.assertEqual(day["projects"][1]["title"], "Updated")
        self.assertEqual(day["updated_at"], "2026-10-15T20:00:00-07:00")

    def test_replace_rewrites_one_day_and_keeps_the_others(self):
        publish(edition("2026-10-15", [project(repo="a/one")]), self.paths)
        publish(edition("2026-10-16", []), self.paths)
        publish(edition("2026-10-15", [project(repo="a/two")]), self.paths, replace=True)
        editions = self.saved()["editions"]
        self.assertEqual([row["day"] for row in editions], ["2026-10-16", "2026-10-15"])
        self.assertEqual([p["repo"] for p in editions[1]["projects"]], ["a/two"])

    def test_invalid_or_off_topic_publication_writes_nothing(self):
        publish(edition("2026-10-15", []), self.paths)
        original = self.paths.editions.read_text(encoding="utf-8")
        for bad in (edition("2026-02-31", []), edition("2026-10-16", [project(topic="not-configured")])):
            with self.subTest(day=bad["day"]), self.assertRaises(ValueError):
                publish(bad, self.paths)
            self.assertEqual(self.paths.editions.read_text(encoding="utf-8"), original)

    def test_unknown_fields_are_rejected_with_a_suggestion(self):
        for bad, hint in ((edition("2026-10-15", [project(fitt="typo")]), "did you mean fit?"),
                          (edition("2026-10-15", [project(stars={"count": 1, "observed_at": "2026-10-15T09:00:00Z", "aprox": True})]), "approximate"),
                          (dict(edition("2026-10-15", []), note="x"), "edition.note")):
            with self.subTest(hint=hint), self.assertRaises(ValueError) as caught:
                publish(bad, self.paths)
            self.assertIn(hint, str(caught.exception))
        self.assertFalse(self.paths.editions.exists())

    def test_check_only_never_writes(self):
        publish(edition("2026-10-15", []), self.paths, check_only=True)
        self.assertFalse(self.paths.editions.exists())

    def test_topics_follow_repomuse_json(self):
        self.paths.config.write_text(json.dumps({"topics": [{"id": "rust", "label": "Rust"}]}), encoding="utf-8")
        self.assertEqual(load_config(self.paths)["topics"][0]["id"], "rust")
        publish(edition("2026-10-15", [project(topic="rust")]), self.paths)
        with self.assertRaises(ValueError):
            publish(edition("2026-10-16", [project(topic="coding")]), self.paths)


    def test_future_times_and_a_second_explore_pick_are_rejected(self):
        future = "2999-01-01T00:00:00+00:00"
        stars = {"count": 1, "observed_at": future}
        explore = [project(repo="a/one", explore=True), project(repo="a/two", explore=True)]
        for bad in (edition("2026-10-15", [], updated_at=future), edition("2026-10-15", [project(stars=stars)]),
                    edition("2999-01-01", []), edition("2026-10-15", explore)):
            with self.subTest(bad=bad["day"]), self.assertRaises(ValueError):
                publish(bad, self.paths)
        self.assertFalse(self.paths.editions.exists())


class DemoAttachTests(StoreTestCase):
    def setUp(self):
        super().setUp()
        (self.paths.demos / "tiny-ui").mkdir(parents=True)
        (self.paths.demos / "tiny-ui" / "index.html").write_text("<p>demo</p>", encoding="utf-8")

    def test_republishing_a_pick_keeps_its_attached_demo(self):
        publish(edition("2026-10-14", [project(repo="a/one")]), self.paths)
        attach_demo("a/one", copy.deepcopy(DEMO), self.paths)
        publish(edition("2026-10-14", [project(repo="a/one", title="Corrected")]), self.paths)
        saved = self.saved()["editions"][0]["projects"][0]
        self.assertEqual((saved["title"], saved["demo"]["status"]), ("Corrected", "ready"))

    def test_ready_demo_needs_its_page_and_a_past_test_time(self):
        publish(edition("2026-10-14", [project(repo="a/one")]), self.paths)
        for bad in (dict(DEMO, path="/demos/not-built/"), dict(DEMO, tested_at="2999-01-01T00:00:00+00:00")):
            with self.subTest(demo=bad["path"]), self.assertRaises(ValueError):
                attach_demo("a/one", bad, self.paths)
        self.assertNotIn("demo", self.saved()["editions"][0]["projects"][0])

    def test_demo_lands_on_the_latest_edition_with_that_repo(self):
        stars = {"count": 10, "observed_at": "2026-10-14T09:00:00-07:00"}
        publish(edition("2026-10-14", [project(repo="a/one", stars=stars)]), self.paths)
        publish(edition("2026-10-16", [project(repo="a/one", event="update")]), self.paths)
        day = attach_demo("A/One", copy.deepcopy(DEMO), self.paths)
        self.assertEqual(day, "2026-10-16")
        editions = self.saved()["editions"]
        self.assertEqual(editions[0]["projects"][0]["demo"]["status"], "ready")
        self.assertNotIn("demo", editions[1]["projects"][0])
        self.assertEqual(editions[1]["projects"][0]["stars"], stars)

    def test_unknown_repo_or_bad_demo_is_rejected(self):
        publish(edition("2026-10-14", [project(repo="a/one")]), self.paths)
        with self.assertRaises(ValueError):
            attach_demo("a/missing", copy.deepcopy(DEMO), self.paths)
        with self.assertRaises(ValueError):
            attach_demo("a/one", dict(DEMO, status="blocked"), self.paths)


class FeedbackTests(StoreTestCase):
    def test_votes_are_saved_lowercased_and_can_be_cleared(self):
        set_vote("Owner/Repo", "like", "Exactly my stack", self.paths)
        votes = load_feedback(self.paths)["votes"]
        self.assertEqual(votes["owner/repo"]["vote"], "like")
        self.assertEqual(votes["owner/repo"]["note"], "Exactly my stack")
        set_vote("owner/repo", None, paths=self.paths)
        self.assertEqual(load_feedback(self.paths)["votes"], {})

    def test_bad_votes_are_rejected(self):
        for repo, value in (("not a repo", "like"), ("a/b", "love")):
            with self.subTest(repo=repo), self.assertRaises(ValueError):
                set_vote(repo, value, paths=self.paths)
        self.assertFalse(self.paths.feedback.exists())


if __name__ == "__main__":
    unittest.main()
