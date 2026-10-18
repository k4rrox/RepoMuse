import contextlib
import io
import json
import socket
import threading
import unittest
from unittest.mock import patch

from repomuse import __main__ as cli
from repomuse import ports, server
from repomuse.config import load_config

from helpers import Checkout


class QuietHandler(server.Handler):
    def log_message(self, *args):
        pass


def free_run(length=6):
    """A start port with `length` ports after it that nothing listens on right now."""
    for _ in range(50):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            start = probe.getsockname()[1]
        if start + length < 65535 and not any(ports.answering(start + step) for step in range(length)):
            return start
    raise unittest.SkipTest("no free run of ports")


@contextlib.contextmanager
def occupied(port):
    holder = socket.socket()
    holder.bind(("127.0.0.1", port))
    holder.listen()
    try:
        yield
    finally:
        holder.close()


class PortChoiceTests(unittest.TestCase):
    def setUp(self):
        self.checkout = Checkout()
        self.paths = self.checkout.paths
        self.start = free_run()
        self.addCleanup(self.checkout.cleanup)

    def write_config(self, **settings):
        self.paths.config.write_text(json.dumps(settings), encoding="utf-8")
        return load_config(self.paths), ports.set_by_user(self.paths)

    def pair(self, config, user_keys, port=None):
        page, demos = ports.open_pair(config, user_keys, port, QuietHandler, QuietHandler)
        for opened in (page, demos):
            opened.server_close()
        return page.server_port, demos.server_port

    def test_a_busy_default_moves_to_the_next_free_pair(self):
        config, user_keys = load_config(self.paths), ports.set_by_user(self.paths)
        config["port"] = self.start  # stands in for the built-in default
        self.assertEqual(user_keys, set())
        with occupied(self.start):
            self.assertEqual(self.pair(config, user_keys), (self.start + 2, self.start + 3))
        with occupied(self.start + 1):  # a busy demo port moves the pair too
            self.assertEqual(self.pair(config, user_keys), (self.start + 2, self.start + 3))

    def test_a_free_default_is_used_as_is(self):
        config = load_config(self.paths)
        config["port"] = self.start
        self.assertEqual(self.pair(config, set()), (self.start, self.start + 1))

    def test_a_port_set_in_repomuse_json_is_never_moved(self):
        config, user_keys = self.write_config(port=self.start)
        self.assertEqual(user_keys, {"port"})
        with occupied(self.start), self.assertRaises(SystemExit) as stopped:
            self.pair(config, user_keys)
        self.assertIn(f"Port {self.start} is already in use", str(stopped.exception))
        self.assertIn('"port" in repomuse.json asks for it', str(stopped.exception))
        with occupied(self.start + 1), self.assertRaises(SystemExit) as stopped:
            self.pair(config, user_keys)
        self.assertIn(f"Port {self.start + 1}", str(stopped.exception))

    def test_a_port_from_the_command_line_is_never_moved(self):
        config = load_config(self.paths)
        with occupied(self.start), self.assertRaises(SystemExit) as stopped:
            self.pair(config, set(), port=self.start)
        self.assertIn("--port", str(stopped.exception))

    def test_a_set_demo_port_is_kept_while_the_page_port_moves(self):
        config, user_keys = self.write_config(demo_port=self.start + 5)
        config["port"] = self.start
        with occupied(self.start):
            self.assertEqual(self.pair(config, user_keys), (self.start + 2, self.start + 5))
        with occupied(self.start + 5), self.assertRaises(SystemExit):
            self.pair(config, user_keys)

    def test_demo_only_server_moves_off_a_busy_default(self):
        config = load_config(self.paths)
        config["port"] = self.start
        with occupied(self.start + 1):
            demos = ports.open_demos(config, set(), None, QuietHandler)
        self.addCleanup(demos.server_close)
        self.assertEqual(demos.server_port, self.start + 3)

    def test_example_config_leaves_the_port_to_repomuse(self):
        example = json.loads((self.paths.examples / "repomuse.example.json").read_text(encoding="utf-8"))
        self.assertNotIn("port", example)
        self.assertNotIn("demo_port", example)


class RunningRecordTests(unittest.TestCase):
    def setUp(self):
        self.checkout = Checkout()
        self.paths = self.checkout.paths
        self.addCleanup(self.checkout.cleanup)
        self.page = ports.LocalServer(("127.0.0.1", 0), QuietHandler)
        self.demos = ports.LocalServer(("127.0.0.1", 0), QuietHandler)
        self.info = ports.record(self.paths, self.page.server_port, self.demos.server_port)
        for httpd in (self.page, self.demos):
            httpd.instance = self.info["instance"]
            httpd.demo_port = self.demos.server_port
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(thread.join)
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)

    def test_the_record_names_the_ports_in_use(self):
        found = ports.running(self.paths)
        self.assertEqual(found["url"], f"http://127.0.0.1:{self.page.server_port}/")
        self.assertEqual(found["demo_url"], f"http://127.0.0.1:{self.demos.server_port}/")

    def test_a_record_from_another_run_is_ignored(self):
        stale = dict(self.info, instance="0" * 16)
        self.paths.server.write_text(json.dumps(stale), encoding="utf-8")
        self.assertIsNone(ports.running(self.paths))
        ports.forget(self.paths, self.info)  # not ours any more: kept
        self.assertTrue(self.paths.server.exists())

    def test_forget_removes_its_own_record(self):
        ports.forget(self.paths, self.info)
        self.assertFalse(self.paths.server.exists())
        self.assertIsNone(ports.running(self.paths))

    def test_status_command(self):
        output = io.StringIO()
        with patch.object(cli, "Paths", lambda: self.paths), contextlib.redirect_stdout(output):
            cli.main(["status", "--json"])
        shown = json.loads(output.getvalue())
        self.assertTrue(shown["running"])
        self.assertEqual(shown["port"], self.page.server_port)
        self.assertNotIn("instance", shown)

    def test_serve_points_to_the_server_already_running(self):
        output = io.StringIO()
        with patch.object(server, "ROOT", self.paths.root), contextlib.redirect_stdout(output):
            server.run()
        self.assertIn(f"already running · {self.info['url']}", output.getvalue())


if __name__ == "__main__":
    unittest.main()
