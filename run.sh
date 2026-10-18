#!/bin/sh
# Start the local page. Optional first argument: port (default from repomuse.json, else 53265).
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ "$#" -gt 0 ]; then exec python3 -B -u -m repomuse serve --port "$1"; fi
exec python3 -B -u -m repomuse serve
