#!/usr/bin/env bash
set -Eeuo pipefail
for doc in README.md README_DE.md DOCKERHUB_README.md examples/docker-compose.yml; do
  grep -Fq 'railsimulatornet/autoheal:latest' "$doc"
done
if grep -E 'autoheal:1\.0([^.]|$)|current 1\.0|aktuelle 1\.0' \
  README.md README_DE.md DOCKERHUB_README.md examples/docker-compose.yml; then
  echo 'Obsolete 1.0 series tag is still referenced.' >&2; exit 1
fi
python3 .github/scripts/test_release_metadata.py -v
