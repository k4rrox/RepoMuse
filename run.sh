#!/bin/sh
# Start the local page and print its address. Optional first argument: use exactly this port
# (default: "port" in repomuse.json, else a free one; `python3 -m repomuse status` shows it later).
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ "$#" -gt 0 ]; then exec python3 -B -u -m repomuse serve --port "$1"; fi
exec python3 -B -u -m repomuse serve
