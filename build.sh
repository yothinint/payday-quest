#!/bin/sh
# Wraps the page source in a full HTML document for GitHub Pages / local testing.
cd "$(dirname "$0")"
{ printf '<!doctype html>\n<html lang="th">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
  cat payday-quest.html
  printf '\n</html>\n'; } > index.html
echo "built index.html"
