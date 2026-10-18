"""Local preview: the picks page, its JSON and feedback write-back on one port, sandboxed demos on the next.

Both bind to 127.0.0.1 only. Demos run on their own origin (port + 1), so they can never read the page's storage
or call its API, without the opaque-origin sandbox that some browsers refuse to load subresources for.
"""
import datetime as dt
import html
import json
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from . import config as config_module
from .config import Paths, demo_port_for, load_config, load_strings
from .store import load_editions, load_feedback, set_vote

ROOT = config_module.ROOT
PAGE = ("index.html", "text/html; charset=utf-8")
ASSETS = {
    "/": PAGE, "/daily": PAGE, "/daily/": PAGE,
    "/app.css": ("app.css", "text/css; charset=utf-8"),
}
DEMO_TYPES = {
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
    ".avif": "image/avif", ".woff": "font/woff", ".woff2": "font/woff2",
}
DEMO_DENIED_PARTS = {"node_modules", "src", "source", "tests", "test", "scripts", "coverage", "__pycache__"}
SCRIPT = re.compile(r"/js/[a-z]+\.js")  # the page's ES modules in web/js/, one level, nothing else
COVER = re.compile(r"/demos/[a-z0-9]+(?:-[a-z0-9]+)*/cover\.(?:jpg|png)")
MAIN_CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; "
            "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
# allow-same-origin keeps the demo port's own origin (never the page's): no forms, popups or top navigation,
# and connect-src 'none' keeps every demo offline.
DEMO_CSP = ("sandbox allow-scripts allow-same-origin; default-src 'none'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; media-src 'self'; "
            "connect-src 'none'; object-src 'none'; base-uri 'none'; frame-src 'none'; frame-ancestors 'none'; "
            "form-action 'none'; worker-src 'none'")
MAX_BODY = 4096


def demo_asset(path):
    """Resolve only preview assets; never expose arbitrary project files or symlinks."""
    decoded = unquote(path)
    if not decoded.startswith("/demos/") or "%" in decoded or "\\" in decoded:
        return None
    parts = decoded[len("/demos/"):].split("/")
    if not parts or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", parts[0]):
        return None
    if parts[-1] == "":
        if len(parts) != 2:
            return None
        parts[-1] = "index.html"
    if len(parts) < 2 or any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", part) or
                             part.lower() in DEMO_DENIED_PARTS for part in parts):
        return None
    base = ROOT / "demos"
    candidate = base
    for part in parts:
        candidate /= part
        if candidate.is_symlink():
            return None
    if base.is_symlink() or base.resolve() not in candidate.resolve().parents:
        return None
    content_type = DEMO_TYPES.get(candidate.suffix.lower())
    if not content_type or (candidate.suffix.lower() == ".html" and parts[1:] != ["index.html"]):
        return None
    return candidate, content_type


def public_config(paths, demo_port):
    config = load_config(paths)
    page = {key: config[key] for key in ("title", "language", "timezone", "cadence", "topics")}
    page["demo_port"] = demo_port
    page["sample"] = not paths.editions.exists()
    page["strings"] = load_strings(paths)
    return page


class Handler(BaseHTTPRequestHandler):
    server_version = "RepoMuse"

    def respond(self, code, body, content_type="application/json; charset=utf-8", head=False, demo=False):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", DEMO_CSP if demo else MAIN_CSP)
        if demo:
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()")
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def local_host(self):
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        return self.headers.get("Host", "") in allowed

    def data_or_error(self, head, loader):
        try:
            return loader()
        except (OSError, ValueError, TypeError) as error:
            print(f"Data did not validate: {error}", flush=True)
            self.respond(422, {"error": f"Data did not validate: {error}"}, head=head)
            return None

    def serve(self, head=False):
        if not self.local_host():
            self.respond(403, {"error": "Only local requests are allowed"}, head=head)
            return
        paths = Paths(ROOT)
        path = urlsplit(self.path).path
        if path == "/favicon.ico":  # the page has no icon; answer quietly instead of logging a 404
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path in ("/api/editions", "/api/daily"):
            data = self.data_or_error(head, lambda: load_editions(paths))
            if data is not None:
                self.respond(200, data, head=head)
        elif path == "/api/config":
            data = self.data_or_error(head, lambda: public_config(paths, self.server.demo_port))
            if data is not None:
                self.respond(200, data, head=head)
        elif path == "/api/feedback":
            data = self.data_or_error(head, lambda: load_feedback(paths))
            if data is not None:
                self.respond(200, data, head=head)
        elif path in ASSETS or SCRIPT.fullmatch(path):
            name, content_type = ASSETS.get(path) or (path.lstrip("/"), "text/javascript; charset=utf-8")
            try:
                body = (paths.web / name).read_bytes()
            except OSError:
                self.respond(404, {"error": "Asset not found"}, head=head)
                return
            self.respond(200, body, content_type, head=head)
        elif COVER.fullmatch(path):
            # Only cover images are served on the page's own origin; the demos themselves live on the demo port.
            self.serve_demo_file(path, head, demo=False)
        else:
            self.respond(404, {"error": "Not found"}, head=head)

    def serve_demo_file(self, path, head, demo):
        asset = demo_asset(path)
        if asset:
            filename, content_type = asset
            try:
                body = filename.read_bytes()
            except OSError:
                pass
            else:
                self.respond(200, body, content_type, head=head, demo=demo)
                return
        self.respond(404, {"error": "Demo asset not found"}, head=head)

    def do_GET(self):
        self.serve()

    def do_HEAD(self):
        self.serve(head=True)

    def do_POST(self):
        """Feedback only. Same-origin JSON from this page; a cross-site form or script cannot pass these checks."""
        if not self.local_host():
            self.respond(403, {"error": "Only local requests are allowed"})
            return
        if urlsplit(self.path).path != "/api/feedback":
            self.respond(404, {"error": "Not found"})
            return
        origin = self.headers.get("Origin")
        if (origin is not None and origin != "http://" + self.headers["Host"]) or \
                self.headers.get("Sec-Fetch-Site", "same-origin") != "same-origin":
            self.respond(403, {"error": "Cross-origin feedback is not accepted"})
            return
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            self.respond(415, {"error": "Send application/json"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if not 0 < length <= MAX_BODY:
            self.respond(413, {"error": "Body is missing or too large"})
            return
        paths = Paths(ROOT)
        if not paths.editions.exists():
            self.respond(409, {"error": "Sample picks: feedback stays in this browser until your first edition"})
            return
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError("body must be an object")
            data = set_vote(body.get("repo"), body.get("vote"), body.get("note"), paths)
        except (ValueError, TypeError, UnicodeDecodeError) as error:
            self.respond(400, {"error": str(error)})
            return
        self.respond(200, data)


def tested_at(project):
    return dt.datetime.fromisoformat(project["demo"]["tested_at"].replace("Z", "+00:00"))


def ready_demos(paths):
    """The latest ready demo per repository, newest first."""
    latest = {}
    for edition in load_editions(paths)["editions"]:
        for project in edition["projects"]:
            demo = project.get("demo")
            if demo and demo["status"] == "ready":
                key = project["repo"].lower()
                if key not in latest or tested_at(project) > tested_at(latest[key]):
                    latest[key] = project
    return sorted(latest.values(), key=tested_at, reverse=True)


def demo_index_page(paths):
    """What "← All demos" shows when only the demo server runs (no-UI mode): a plain list, no script."""
    items = "".join(
        f'<li><a href="{html.escape(project["demo"]["path"])}">{html.escape(project["demo"]["title"])}</a>'
        f'<span>{html.escape(project["name"])} · {html.escape(project["demo"]["summary"])}</span></li>'
        for project in ready_demos(paths)) or "<li><span>No verified demos yet.</span></li>"
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Demos · RepoMuse</title>"
            "<style>body{margin:0;background:#f3f3f0;color:#17181b;font:16px/1.6 -apple-system,BlinkMacSystemFont,"
            "\"PingFang SC\",\"Microsoft YaHei\",sans-serif}main{max-width:760px;margin:0 auto;padding:40px 16px}"
            "h1{font-size:32px;margin:0 0 24px}ul{list-style:none;margin:0;padding:0;display:grid;gap:12px}"
            "li{background:#fff;border-radius:10px;padding:18px 22px}a{color:#0f5132;font-weight:650;font-size:18px}"
            "span{display:block;color:#474a51;font-size:14px}</style></head>"
            f"<body><main><h1>Demos</h1><ul>{items}</ul></main></body></html>").encode("utf-8")


class DemoHandler(Handler):
    """The demo origin: preview assets only. No API, no page, no writes."""

    def serve(self, head=False):
        if not self.local_host():
            self.respond(403, {"error": "Only local requests are allowed"}, head=head)
            return
        parts = urlsplit(self.path)
        if parts.path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif parts.path in ("/", "/daily", "/daily/") and self.server.main_port is None:
            page = self.data_or_error(head, lambda: demo_index_page(Paths(ROOT)))
            if page is not None:
                self.respond(200, page, "text/html; charset=utf-8", head=head, demo=True)
        elif parts.path in ("/", "/daily", "/daily/"):
            # Demo bars link back to "/?view=demos"; send them to the page on its own port.
            host = self.headers["Host"].rsplit(":", 1)[0]
            target = f"http://{host}:{self.server.main_port}/" + (f"?{parts.query}" if parts.query else "")
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif parts.path.startswith("/demos/"):
            self.serve_demo_file(parts.path, head, demo=True)
        else:
            self.respond(404, {"error": "Not found"}, head=head)

    def do_POST(self):
        self.respond(405, {"error": "Demos are read-only"})


def run_demos(port=None, slug=None, open_browser=True):
    """No-UI mode: only the demo origin, until Ctrl-C. `slug` opens that demo; otherwise the demo list."""
    paths = Paths(ROOT)
    try:
        config = load_config(paths)
    except (OSError, ValueError) as error:
        raise SystemExit(f"repomuse.json is not valid: {error}")
    demo_port = demo_port_for(config, port)
    if slug and not (paths.demos / slug / "index.html").is_file():
        raise SystemExit(f"demos/{slug}/index.html does not exist")
    try:
        demos = ThreadingHTTPServer(("127.0.0.1", demo_port), DemoHandler)
    except OSError as error:
        raise SystemExit(f"Could not start on port {demo_port}: {error}. Is ./run.sh already serving demos there?")
    demos.main_port = None
    url = f"http://127.0.0.1:{demo_port}/" + (f"demos/{slug}/" if slug else "")
    print(f"RepoMuse demos · {url}  (Ctrl-C to stop)", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        demos.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        demos.server_close()


def run(port=None):
    paths = Paths(ROOT)
    try:
        config = load_config(paths)
    except (OSError, ValueError) as error:
        raise SystemExit(f"repomuse.json is not valid: {error}")
    port = port or config["port"]
    demo_port = demo_port_for(config, port)
    servers = []
    for number, handler in ((port, Handler), (demo_port, DemoHandler)):
        try:
            servers.append(ThreadingHTTPServer(("127.0.0.1", number), handler))
        except OSError as error:
            for started in servers:
                started.server_close()
            raise SystemExit(f"Could not start on port {number}: {error}. Try ./run.sh {port + 2}")
    main, demos = servers
    main.demo_port, demos.main_port = demo_port, port
    threading.Thread(target=demos.serve_forever, daemon=True).start()
    print(f"RepoMuse · http://127.0.0.1:{port}/  (demos on port {demo_port})", flush=True)
    try:
        main.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        demos.shutdown()
        for server in servers:
            server.server_close()
