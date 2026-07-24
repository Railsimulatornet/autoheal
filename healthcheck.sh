#!/bin/sh
set -eu

DOCKER_SOCK="${DOCKER_SOCK:-/var/run/docker.sock}"
HEARTBEAT_FILE="${AUTOHEAL_HEARTBEAT_FILE:-/tmp/autoheal-heartbeat}"
INTERVAL="${AUTOHEAL_INTERVAL:-30}"

case "$INTERVAL" in
    ""|*[!0-9]*) exit 1 ;;
esac

[ -S "$DOCKER_SOCK" ]
[ -f "$HEARTBEAT_FILE" ]

now="$(date +%s)"
modified="$(stat -c '%Y' "$HEARTBEAT_FILE")"
maximum_age=$((INTERVAL * 3 + 30))
age=$((now - modified))

[ "$age" -le "$maximum_age" ]
