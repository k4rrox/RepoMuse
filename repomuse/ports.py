"""Which ports the local servers use, and where the running ones are recorded (work/server.json).

The default ports stay the same from run to run on purpose: the browser keeps sample votes and unsent
feedback per origin, and bookmarks and links the agent shared keep working. A busy default moves on to the
next free pair. A port you set yourself (in repomuse.json or with --port) is used as is, or the command stops
and says why.
"""
import datetime as dt
import json
import os
import secrets
import socket
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from .config import demo_port_for
from .store import write_json

ATTEMPTS = 20  # pairs tried after a busy default: port, port + 2, port + 4, ...
INSTANCE_HEADER = "X-RepoMuse-Instance"


class LocalServer(ThreadingHTTPServer):
    # SO_REUSEADDR lets a restart take its port back at once on macOS and Linux. On Windows it would let two
    # servers share one port, so it stays off there.
    allow_reuse_address = os.name != "nt"


def answering(port):
    """Something already accepts connections on 127.0.0.1:port, even a server bound to all interfaces."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def open_server(port, handler):
    if answering(port):
        return None
    try:
        return LocalServer(("127.0.0.1", port), handler)
    except OSError:
        return None


def set_by_user(paths):
    """The port keys written in repomuse.json itself, as opposed to the defaults."""
    if not paths.config.exists():
        return set()
    user = json.loads(paths.config.read_text(encoding="utf-8"))
    return {key for key in ("port", "demo_port") if isinstance(user, dict) and key in user}


def busy(port, key, from_command_line):
    if from_command_line and key == "port":
        return SystemExit(f"Port {port} is already in use. Stop what uses it, or pass another --port "
                          f"(leave it out and RepoMuse picks a free one).")
    return SystemExit(f"Port {port} is already in use, and \"{key}\" in repomuse.json asks for it. Stop what uses "
                      f"it, or change \"{key}\" (leave it out and RepoMuse picks a free one).")


def candidates(first, fixed):
    return [first] if fixed else [first + 2 * step for step in range(ATTEMPTS)]


def open_pair(config, user_keys, port, page_handler, demo_handler):
    """The page and demo servers. `port` comes from --port; None means repomuse.json or the default."""
    fixed_page = port is not None or "port" in user_keys
    fixed_demo = fixed_page or "demo_port" in user_keys
    first = port or config["port"]
    for page_port in candidates(first, fixed_page):
        demo_port = demo_port_for(config, page_port)
        page = open_server(page_port, page_handler)
        if page is None:
            if fixed_page:
                raise busy(page_port, "port", port is not None)
            continue
        demos = open_server(demo_port, demo_handler)
        if demos is None:
            page.server_close()
            if fixed_demo:
                raise busy(demo_port, "demo_port", False)
            continue
        return page, demos
    raise SystemExit(f"No free pair of ports from {first} on. Set a free \"port\" in repomuse.json.")


def open_demos(config, user_keys, port, handler):
    """The demo server alone (no-UI mode)."""
    fixed = port is not None or bool(user_keys)
    first = demo_port_for(config, port)
    for demo_port in candidates(first, fixed):
        demos = open_server(demo_port, handler)
        if demos is not None:
            return demos
        if fixed:
            raise busy(demo_port, "demo_port" if "demo_port" in user_keys else "port", port is not None)
    raise SystemExit(f"No free port from {first} on. Set a free \"demo_port\" in repomuse.json.")


def record(paths, page_port, demo_port):
    """Write work/server.json so agents and commands find the servers on the ports actually used."""
    info = {
        "url": f"http://127.0.0.1:{page_port}/" if page_port else None,
        "port": page_port,
        "demo_url": f"http://127.0.0.1:{demo_port}/",
        "demo_port": demo_port,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "instance": secrets.token_hex(8),
    }
    write_json(paths.server, info)
    return info


def read_record(paths):
    try:
        info = json.loads(paths.server.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return info if isinstance(info, dict) else None


def forget(paths, info):
    """Remove the record on shutdown, unless a newer server has replaced it."""
    current = read_record(paths)
    if current and current.get("instance") == info["instance"]:
        try:
            paths.server.unlink()
        except OSError:
            pass


def running(paths):
    """The recorded servers if they still answer as that same instance, else None (a stale record)."""
    info = read_record(paths)
    try:
        port = info.get("port") or info["demo_port"]
        connection = HTTPConnection("127.0.0.1", port, timeout=1)
        try:
            connection.request("HEAD", "/favicon.ico")
            instance = connection.getresponse().getheader(INSTANCE_HEADER)
        finally:
            connection.close()
    except (OSError, AttributeError, KeyError, TypeError, ValueError):
        return None
    return info if instance and instance == info.get("instance") else None
