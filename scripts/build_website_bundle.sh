#!/bin/bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 OUTPUT_TGZ" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WEBSITE_DIR="$REPO_DIR/website"
OUTPUT_TGZ="$1"

mkdir -p "$(dirname "$OUTPUT_TGZ")"
OUTPUT_DIR="$(cd "$(dirname "$OUTPUT_TGZ")" && pwd)"
OUTPUT_TGZ="$OUTPUT_DIR/$(basename "$OUTPUT_TGZ")"

cd "$WEBSITE_DIR"
npm ci
npm run build
rm -f "$OUTPUT_TGZ"
COPYFILE_DISABLE=1 tar -czf "$OUTPUT_TGZ" -C "$WEBSITE_DIR/out" .
