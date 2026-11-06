#!/usr/bin/env bash
set -euo pipefail

# Project Gutenberg eBook 148: The Autobiography of Benjamin Franklin.
# This is a public-domain text. Keep the source URL explicit and pinned so
# future refreshes are reproducible and easy to audit.
SOURCE_URL="https://www.gutenberg.org/cache/epub/148/pg148.txt"
OUTPUT_FILE="${1:-content/franklin-autobiography.txt}"

mkdir -p "$(dirname "$OUTPUT_FILE")"
tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

curl --fail --location --retry 3 --silent --show-error "$SOURCE_URL" -o "$tmp_file"

# Normalize line endings while preserving the book's paragraph structure.
tr -d '\r' < "$tmp_file" > "$OUTPUT_FILE"
python3 scripts/build-book.py "$OUTPUT_FILE"

printf 'Downloaded %s (%s bytes)\n' "$OUTPUT_FILE" "$(wc -c < "$OUTPUT_FILE" | tr -d ' ')"
