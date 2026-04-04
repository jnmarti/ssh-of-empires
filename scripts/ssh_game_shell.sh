#!/bin/zsh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GAME_PATH="/usr/bin:/bin:/usr/sbin:/sbin"
GAME_TERM="${TERM:-xterm-256color}"
GAME_LANG="${LANG:-C.UTF-8}"
GAME_LC_ALL="${LC_ALL:-C.UTF-8}"
GAME_USER="${USER:-player}"
cd "$REPO_DIR"

umask 077
exec env -i \
  HOME="$HOME" \
  USER="$GAME_USER" \
  LOGNAME="$GAME_USER" \
  PATH="$GAME_PATH" \
  TERM="$GAME_TERM" \
  LANG="$GAME_LANG" \
  LC_ALL="$GAME_LC_ALL" \
  python3 "$REPO_DIR/aoe_terminal.py"
