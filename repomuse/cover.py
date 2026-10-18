"""Capture demos/<slug>/cover.png with headless Chrome or Chromium. Pure standard library, any OS.

The page is rendered taller than the cover, then the PNG is cropped `offset` CSS pixels down so the
interactive part, not the page title, fills the thumbnail. On macOS `sips` also writes a smaller cover.jpg.
"""
import os
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

WIDTH, HEIGHT, SCALE = 1280, 800, 0.75
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
CHROME_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"]


def find_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    for command in CHROME_COMMANDS:
        if shutil.which(command):
            return shutil.which(command)
    return None


def _chunks(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    position = 8
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position:position + 8])
        yield kind, data[position + 8:position + 8 + length]
        position += 12 + length


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def crop_png_rows(data, top, height):
    """Keep `height` rows from `top` of an 8-bit RGB/RGBA, non-interlaced PNG."""
    header, compressed = None, b""
    for kind, body in _chunks(data):
        if kind == b"IHDR":
            header = body
        elif kind == b"IDAT":
            compressed += body
    width, total, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", header)
    if depth != 8 or color not in (2, 6) or interlace:
        raise ValueError("only 8-bit RGB/RGBA non-interlaced PNGs are supported")
    channels = 3 if color == 2 else 4
    stride = width * channels
    raw = zlib.decompress(compressed)
    top = max(0, min(top, total - 1))
    bottom = min(total, top + height)
    previous = bytearray(stride)
    rows = []
    for row in range(bottom):
        start = row * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            left = line[i - channels] if i >= channels else 0
            up = previous[i]
            if kind == 1:
                line[i] = (line[i] + left) & 0xFF
            elif kind == 2:
                line[i] = (line[i] + up) & 0xFF
            elif kind == 3:
                line[i] = (line[i] + ((left + up) >> 1)) & 0xFF
            elif kind == 4:
                line[i] = (line[i] + _paeth(left, up, previous[i - channels] if i >= channels else 0)) & 0xFF
        if row >= top:
            rows.append(b"\x00" + bytes(line))
        previous = line

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, len(rows), 8, color, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")


def capture(slug, demo_port, demos_dir, offset=0):
    chrome = find_chrome()
    if not chrome:
        raise SystemExit("No Chrome, Chromium or Edge found. Set CHROME=/path/to/browser, or skip the cover: "
                         "cards fall back to text.")
    out_dir = Path(demos_dir) / slug
    if not (out_dir / "index.html").is_file():
        raise SystemExit(f"demos/{slug}/index.html does not exist")
    with tempfile.TemporaryDirectory() as tmp:
        shot = Path(tmp) / "shot.png"
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
                        f"--user-data-dir={Path(tmp) / 'profile'}", f"--window-size={WIDTH},{HEIGHT + offset}",
                        "--virtual-time-budget=5000", f"--screenshot={shot}", f"http://127.0.0.1:{demo_port}/demos/{slug}/"],
                       check=True, capture_output=True, timeout=120)
        png = out_dir / "cover.png"
        png.write_bytes(crop_png_rows(shot.read_bytes(), round(offset * SCALE), round(HEIGHT * SCALE)))
    if shutil.which("sips"):
        jpg = out_dir / "cover.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "78", str(png), "--out", str(jpg)],
                       check=True, capture_output=True)
        png.unlink()
        return jpg
    return png
