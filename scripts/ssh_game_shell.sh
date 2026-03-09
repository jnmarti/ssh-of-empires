#!/bin/zsh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

export TERM="${TERM:-xterm-256color}"
exec python3 "$REPO_DIR/aoe_terminal.py"
