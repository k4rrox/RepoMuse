import contextlib
import io
import json
import struct
import unittest
import zlib
from unittest.mock import patch

from repomuse import __main__ as cli
from repomuse.config import Paths
from repomuse.cover import crop_png_rows

from helpers import Checkout, edition, project


class CliTests(unittest.TestCase):
    def setUp(self):
        self.checkout = Checkout()
        self.patch = patch.object(cli, "Paths", lambda: Paths(self.checkout.root))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.checkout.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def write(self, name, data):
        path = self.checkout.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def test_init_check_publish_seen_and_feedback(self):
        self.assertEqual(self.run_cli("init")[0], 0)
        self.assertTrue((self.checkout.root / "profile.md").exists())
        self.assertIn("kept", self.run_cli("init")[1])
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("bundled sample", out)
        path = self.write("edition.json", edition("2026-10-15", [project(repo="a/one")]))
        self.assertEqual(self.run_cli("publish", path, "--check")[0], 0)
        self.assertFalse(self.checkout.paths.editions.exists())
        self.assertEqual(self.run_cli("publish", path)[0], 0)
        seen = json.loads(self.run_cli("seen", "--json")[1])
        self.assertEqual(seen[0]["repo"], "a/one")
        self.assertEqual(json.loads(self.run_cli("feedback", "--json")[1]), [])

    def test_check_reports_missing_or_broken_translations(self):
        self.write("repomuse.json", {"language": "zh-CN"})
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("strings.json is missing", out)
        self.write("strings.json", {"verdict.try": "值得试用", "shown": "显示 {n}"})
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("'shown' must keep the placeholders", out)
        self.write("strings.json", {"verdict.try": "值得试用"})
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("interface strings translated", out)

    def test_errors_are_reported_without_a_traceback(self):
        path = self.write("bad.json", {"day": "nope"})
        code, _, err = self.run_cli("publish", path)
        self.assertEqual(code, 1)
        self.assertIn("day must be YYYY-MM-DD", err)

    def test_migrate_from_open_source_radar(self):
        old = {"schema_version": 1, "timezone": "America/Los_Angeles", "demo": False,
               "editions": [edition("2026-10-15")]}
        code, out, _ = self.run_cli("migrate", self.write("daily.json", old))
        self.assertEqual(code, 0)
        self.assertIn("America/Los_Angeles", out)
        data = json.loads(self.checkout.paths.editions.read_text(encoding="utf-8"))
        self.assertEqual((data["schema_version"], data["sample"]), (2, False))
        self.assertEqual(self.run_cli("migrate", self.write("daily.json", old))[0], 1)  # refuses to overwrite

    def test_no_ui_digest_and_vote(self):
        self.assertEqual(self.run_cli("init")[0], 0)
        self.assertTrue((self.checkout.root / "work").is_dir())
        code, _, err = self.run_cli("vote", "a/one", "like")
        self.assertEqual(code, 1)
        self.assertIn("sample picks", err)
        code, out, _ = self.run_cli("digest")
        self.assertEqual(code, 0)
        self.assertIn("_Sample picks:", out)
        self.run_cli("publish", self.write("edition.json", edition("2026-10-15", [project(repo="a/one")])))
        out_file = self.checkout.root / "work" / "digest.md"
        code, out, _ = self.run_cli("digest", "--out", str(out_file))
        self.assertEqual(code, 0)
        self.assertIn("### 1. [Test](https://github.com/a/one)", out)
        self.assertEqual(out_file.read_text(encoding="utf-8"), out)
        self.assertIn("Saved a/one: like", self.run_cli("vote", "a/one", "like", "--note", "my stack")[1])
        self.assertIn("not in any published edition", self.run_cli("vote", "b/other", "dislike")[1])
        out = self.run_cli("vote", "b/other", "dislike", "--reason", "too-heavy", "--reason", "already-known")[1]
        self.assertIn("(too-heavy, already-known)", out)
        rows = {row["repo"]: row for row in json.loads(self.run_cli("feedback", "--json")[1])}
        self.assertEqual(rows["b/other"]["reasons"], ["too-heavy", "already-known"])
        self.assertIn("too-heavy, already-known", self.run_cli("feedback")[1])
        with self.assertRaises(SystemExit):  # argparse rejects unknown reason codes
            self.run_cli("vote", "b/other", "dislike", "--reason", "boring")
        rows = {row["repo"]: row for row in json.loads(self.run_cli("feedback", "--json")[1])}
        self.assertEqual((rows["a/one"]["vote"], rows["a/one"]["note"]), ("like", "my stack"))
        self.assertEqual(self.run_cli("vote", "a/one", "clear")[0], 0)
        self.assertNotIn("a/one", {row["repo"] for row in json.loads(self.run_cli("feedback", "--json")[1])})
        self.assertEqual(self.run_cli("digest", "--day", "2026-01-01")[0], 1)


def png(width, height, rows):
    raw = b"".join(bytes([filt]) + row for filt, row in rows)
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def decode_rows(data):
    position, idat, header = 8, b"", None
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position:position + 8])
        body = data[position + 8:position + 8 + length]
        header = body if kind == b"IHDR" else header
        idat += body if kind == b"IDAT" else b""
        position += 12 + length
    width, height = struct.unpack(">II", header[:8])
    raw = zlib.decompress(idat)
    stride = width * 3
    return [raw[i * (stride + 1) + 1:(i + 1) * (stride + 1)] for i in range(height)]


class CoverCropTests(unittest.TestCase):
    def test_filtered_rows_are_reconstructed_before_cropping(self):
        # Row 0 is plain; row 1 uses the "up" filter (+10 on every byte); row 2 uses "sub".
        rows = [(0, bytes([10, 20, 30, 40, 50, 60])), (2, bytes([10] * 6)), (1, bytes([5, 5, 5, 1, 1, 1]))]
        cropped = crop_png_rows(png(2, 3, rows), 1, 2)
        self.assertEqual(decode_rows(cropped), [bytes([20, 30, 40, 50, 60, 70]), bytes([5, 5, 5, 6, 6, 6])])


if __name__ == "__main__":
    unittest.main()
