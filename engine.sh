#!/usr/bin/env bash
# Thin wrapper for the statusline engine. Finds python3 and runs engine.py,
# passing stdin (the Claude Code JSON payload) through. Lives in the skill dir;
# state (active profile, profiles/) lives in $HOME/.claude/statusline.
# If python3 is missing, prints nothing rather than breaking the terminal.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
    exit 0
fi
exec "$PY" "$DIR/engine.py" "$@"
