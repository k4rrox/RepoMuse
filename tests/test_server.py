import json
import os
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from repomuse import server
from repomuse.store import publish

from helpers import Checkout, edition


class QuietHandler(server.Handler):
    def log_message(self, *args):
        pass


class QuietDemoHandler(server.DemoHandler):
    def log_message(self, *args):
        pass


class ServerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkout = Checkout()
        cls.root = cls.checkout.root
        cls.patch_root = patch.object(server, "ROOT", cls.root)
        cls.patch_root.start()
        demo = cls.root / "demos" / "tiny-ui"
        (demo / "node_modules").mkdir(parents=True)
        (demo / "index.html").write_text('<script type="module" src="./app.js"></script>', encoding="utf-8")
        (demo / "app.js").write_text("document.body.dataset.loaded = 'yes';", encoding="utf-8")
        (demo / "app.css").write_text("body{color:blue}", encoding="utf-8")
        (demo / "cover.jpg").write_bytes(b"\xff\xd8\xff\xe0cover")
        for private in ("secret.json", "README.md", "server.py", ".env", "other.html", "node_modules/app.js"):
            (demo / private).write_text("private", encoding="utf-8")
        cls.symlinks = True
        try:
            outside = cls.root / "outside.js"
            outside.write_text("private", encoding="utf-8")
            (demo / "linked.js").symlink_to(outside)
            (cls.root / "demos" / "linked-demo").symlink_to(demo, target_is_directory=True)
        except (OSError, NotImplementedError):  # Windows without symlink privilege
            cls.symlinks = False
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.demo_httpd = ThreadingHTTPServer(("127.0.0.1", 0), QuietDemoHandler)
        cls.port, cls.demo_port = cls.httpd.server_port, cls.demo_httpd.server_port
        cls.httpd.demo_port, cls.demo_httpd.main_port = cls.demo_port, cls.port
        cls.threads = [threading.Thread(target=httpd.serve_forever, daemon=True) for httpd in (cls.httpd, cls.demo_httpd)]
        for thread in cls.threads:
            thread.start()

    @classmethod
    def tearDownClass(cls):
        for httpd in (cls.httpd, cls.demo_httpd):
            httpd.shutdown()
            httpd.server_close()
        for thread in cls.threads:
            thread.join()
        cls.patch_root.stop()
        cls.checkout.cleanup()

    def request(self, path, method="GET", host=None, body=None, headers=None, demo=False):
        port = self.demo_port if demo else self.port
        connection = HTTPConnection("127.0.0.1", port)
        all_headers = {"Host": host or f"127.0.0.1:{port}"}
        all_headers.update(headers or {})
        connection.request(method, path, body=body, headers=all_headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def post_vote(self, payload, **headers):
        body = json.dumps(payload).encode()
        merged = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{self.port}"}
        merged.update(headers)
        return self.request("/api/feedback", "POST", body=body, headers={k: v for k, v in merged.items() if v is not None})


class DemoServingTests(ServerTestCase):
    def test_preview_html_scripts_and_styles_are_served_sandboxed_on_the_demo_port(self):
        for path, content_type in (("/demos/tiny-ui/", "text/html"), ("/demos/tiny-ui/index.html", "text/html"),
                                   ("/demos/tiny-ui/app.js", "text/javascript"), ("/demos/tiny-ui/app.css", "text/css")):
            code, headers, body = self.request(path, demo=True)
            self.assertEqual(code, 200, path)
            self.assertTrue(headers["Content-Type"].startswith(content_type))
            self.assertTrue(body)
            csp = headers["Content-Security-Policy"]
            self.assertTrue(csp.startswith("sandbox allow-scripts allow-same-origin;"))
            for blocked in ("allow-forms", "allow-popups", "allow-top-navigation", "allow-modals"):
                self.assertNotIn(blocked, csp)
            for rule in ("connect-src 'none'", "form-action 'none'", "frame-ancestors 'none'", "script-src 'self';"):
                self.assertIn(rule, csp)
            self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_page_port_serves_only_covers_and_demo_port_serves_no_page_or_api(self):
        code, headers, _ = self.request("/demos/tiny-ui/cover.jpg")
        self.assertEqual(code, 200)
        self.assertNotIn("sandbox", headers["Content-Security-Policy"])
        for path in ("/demos/tiny-ui/", "/demos/tiny-ui/app.js"):
            self.assertEqual(self.request(path)[0], 404, path)
        for path in ("/api/editions", "/api/config", "/api/feedback", "/app.js"):
            self.assertEqual(self.request(path, demo=True)[0], 404, path)
        self.assertEqual(self.request("/api/feedback", "POST", body=b"{}", demo=True,
                                      headers={"Content-Type": "application/json"})[0], 405)

    def test_demo_port_sends_back_links_to_the_page(self):
        code, headers, _ = self.request("/?view=demos", demo=True, host=f"localhost:{self.demo_port}")
        self.assertEqual(code, 302)
        self.assertEqual(headers["Location"], f"http://localhost:{self.port}/?view=demos")

    def test_standalone_demo_server_lists_demos_instead_of_redirecting(self):
        self.demo_httpd.main_port = None
        try:
            code, headers, body = self.request("/?view=demos", demo=True)
            self.assertEqual(code, 200)
            self.assertTrue(headers["Content-Security-Policy"].startswith("sandbox"))
            self.assertIn(b'href="/demos/taste-skill/"', body)
            self.assertNotIn(b"<script", body)
        finally:
            self.demo_httpd.main_port = self.port
        self.assertEqual(self.request("/favicon.ico", demo=True)[0], 204)

    def test_feedback_from_the_demo_origin_is_rejected(self):
        publish(edition("2026-10-15", []), self.checkout.paths)
        try:
            for headers in ({"Origin": f"http://127.0.0.1:{self.demo_port}"}, {"Sec-Fetch-Site": "same-site"}):
                with self.subTest(headers=headers):
                    self.assertEqual(self.post_vote({"repo": "a/b", "vote": "like"}, **headers)[0], 403)
        finally:
            os.remove(self.checkout.paths.editions)

    def test_nonpreview_files_and_escape_paths_are_denied(self):
        paths = ["/demos/tiny-ui/../outside.js", "/demos/tiny-ui/%2e%2e/outside.js",
                 "/demos/tiny-ui/%252e%252e/outside.js", "/demos/tiny-ui//app.js",
                 "/demos/tiny-ui/%5capp.js", "/demos/tiny-ui/.env", "/demos/tiny-ui/secret.json",
                 "/demos/tiny-ui/README.md", "/demos/tiny-ui/server.py", "/demos/tiny-ui/node_modules/app.js",
                 "/demos/tiny-ui/other.html", "/demos/tiny-ui/no-file.png"]
        if self.symlinks:
            paths += ["/demos/tiny-ui/linked.js", "/demos/linked-demo/"]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.request(path, demo=True)[0], 404)

    def test_main_page_keeps_its_own_policy_and_foreign_host_is_rejected(self):
        for path in ("/", "/daily", "/js/main.js", "/js/strings.js", "/mark.svg"):
            code, headers, _ = self.request(path)
            self.assertEqual(code, 200, path)
            self.assertNotIn("sandbox", headers["Content-Security-Policy"])
            self.assertNotIn("unsafe-inline", headers["Content-Security-Policy"])
            self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(self.request("/demos/tiny-ui/", host="attacker.test", demo=True)[0], 403)
        self.assertEqual(self.request("/demos/tiny-ui/", host=f"127.0.0.1:{self.port}", demo=True)[0], 403)
        self.assertEqual(self.request("/api/editions", host=f"evil.test:{self.port}")[0], 403)
        for path in ("/app.js", "/js/package.json", "/js/../index.html", "/js/missing.js", "/js/Main.js", "/js/sub/main.js"):
            self.assertEqual(self.request(path)[0], 404, path)

    def test_head_has_no_body(self):
        code, headers, body = self.request("/demos/tiny-ui/", method="HEAD", demo=True)
        self.assertEqual(code, 200)
        self.assertGreater(int(headers["Content-Length"]), 0)
        self.assertEqual(body, b"")


class ApiTests(ServerTestCase):
    def tearDown(self):
        for path in (self.checkout.paths.editions, self.checkout.paths.feedback, self.checkout.paths.config):
            if path.exists():
                os.remove(path)

    def test_config_and_sample_editions(self):
        code, _, body = self.request("/api/config")
        config = json.loads(body)
        self.assertEqual(code, 200)
        self.assertTrue(config["sample"])
        self.assertIn("topics", config)
        self.assertNotIn("port", config)
        self.assertEqual(config["demo_port"], self.demo_port)
        editions = json.loads(self.request("/api/editions")[2])
        self.assertTrue(editions["sample"])
        self.assertEqual(json.loads(self.request("/api/daily")[2]), editions)

    def test_invalid_config_is_reported_not_crashed(self):
        self.checkout.paths.config.write_text('{"language": "not a tag"}', encoding="utf-8")
        self.assertEqual(self.request("/api/config")[0], 422)

    def test_agent_written_strings_are_served_with_the_config(self):
        self.checkout.paths.config.write_text('{"language": "zh-CN"}', encoding="utf-8")
        self.checkout.paths.strings.write_text('{"nav.picks": "精选"}', encoding="utf-8")
        try:
            config = json.loads(self.request("/api/config")[2])
            self.assertEqual((config["language"], config["strings"]), ("zh-CN", {"nav.picks": "精选"}))
            self.checkout.paths.strings.write_text('{"nav.picks": 3}', encoding="utf-8")
            self.assertEqual(self.request("/api/config")[0], 422)
        finally:
            os.remove(self.checkout.paths.strings)

    def test_feedback_is_refused_for_sample_picks(self):
        self.assertEqual(self.post_vote({"repo": "a/b", "vote": "like"})[0], 409)

    def test_feedback_round_trip(self):
        publish(edition("2026-10-15", []), self.checkout.paths)
        code, _, body = self.post_vote({"repo": "Owner/Repo", "vote": "like"})
        self.assertEqual(code, 200, body)
        votes = json.loads(self.request("/api/feedback")[2])["votes"]
        self.assertEqual(votes["owner/repo"]["vote"], "like")
        self.assertEqual(self.post_vote({"repo": "owner/repo", "vote": None})[0], 200)
        self.assertEqual(json.loads(self.request("/api/feedback")[2])["votes"], {})

    def test_cross_site_and_malformed_feedback_is_rejected(self):
        publish(edition("2026-10-15", []), self.checkout.paths)
        vote = {"repo": "a/b", "vote": "like"}
        self.assertEqual(self.post_vote(vote, Origin="https://evil.test")[0], 403)
        self.assertEqual(self.post_vote(vote, **{"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.post_vote(vote, **{"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.post_vote({"repo": "a/b", "vote": "love"})[0], 400)
        self.assertEqual(self.post_vote({"repo": "a/b", "note": "x" * 5000, "vote": "like"})[0], 413)
        self.assertEqual(self.request("/api/feedback", "POST", host="evil.test", body=b"{}",
                                      headers={"Content-Type": "application/json"})[0], 403)
        self.assertEqual(json.loads(self.request("/api/feedback")[2])["votes"], {})


if __name__ == "__main__":
    unittest.main()
