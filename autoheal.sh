#!/bin/sh
set -eu

LABEL_KEY="${AUTOHEAL_CONTAINER_LABEL:-autoheal}"
LABEL_VALUE="${AUTOHEAL_CONTAINER_LABEL_VALUE:-true}"
INTERVAL="${AUTOHEAL_INTERVAL:-30}"
START_PERIOD="${AUTOHEAL_START_PERIOD:-120}"
STOP_TIMEOUT="${AUTOHEAL_DEFAULT_STOP_TIMEOUT:-10}"
COOLDOWN="${AUTOHEAL_COOLDOWN:-300}"
MAX_RESTARTS="${AUTOHEAL_MAX_RESTARTS:-3}"
RESTART_WINDOW="${AUTOHEAL_RESTART_WINDOW:-1800}"
DRY_RUN="${AUTOHEAL_DRY_RUN:-false}"
LOG_LEVEL="${AUTOHEAL_LOG_LEVEL:-info}"
STATE_DIR="${AUTOHEAL_STATE_DIR:-/state}"
HEARTBEAT_FILE="${AUTOHEAL_HEARTBEAT_FILE:-/tmp/autoheal-heartbeat}"
DOCKER_SOCK="${DOCKER_SOCK:-/var/run/docker.sock}"

export DOCKER_HOST="${DOCKER_HOST:-unix://${DOCKER_SOCK}}"

log() {
    level="$1"
    shift
    printf '%s [%s] %s\n' "$(date -Iseconds)" "$level" "$*"
}

debug() {
    if [ "$LOG_LEVEL" = "debug" ]; then
        log "DEBUG" "$*"
    fi
}

is_uint() {
    case "$1" in
        ""|*[!0-9]*) return 1 ;;
        *) return 0 ;;
    esac
}

validate_uint() {
    name="$1"
    value="$2"

    if ! is_uint "$value"; then
        log "ERROR" "$name muss eine nichtnegative Ganzzahl sein: $value"
        exit 2
    fi
}

validate_uint "AUTOHEAL_INTERVAL" "$INTERVAL"
validate_uint "AUTOHEAL_START_PERIOD" "$START_PERIOD"
validate_uint "AUTOHEAL_DEFAULT_STOP_TIMEOUT" "$STOP_TIMEOUT"
validate_uint "AUTOHEAL_COOLDOWN" "$COOLDOWN"
validate_uint "AUTOHEAL_MAX_RESTARTS" "$MAX_RESTARTS"
validate_uint "AUTOHEAL_RESTART_WINDOW" "$RESTART_WINDOW"

if [ "$INTERVAL" -lt 1 ]; then
    log "ERROR" "AUTOHEAL_INTERVAL muss mindestens 1 sein."
    exit 2
fi

case "$(printf '%s' "$DRY_RUN" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) DRY_RUN="true" ;;
    *) DRY_RUN="false" ;;
esac

mkdir -p "$STATE_DIR"
date +%s > "$HEARTBEAT_FILE"

log "INFO" "Autoheal gestartet"
log "INFO" "Docker: $DOCKER_HOST"
log "INFO" "Filter: ${LABEL_KEY}=${LABEL_VALUE}"
log "INFO" "Intervall: ${INTERVAL}s"
log "INFO" "Startphase: ${START_PERIOD}s"
log "INFO" "Cooldown: ${COOLDOWN}s"
log "INFO" "Restart-Limit: ${MAX_RESTARTS} je ${RESTART_WINDOW}s"
log "INFO" "Dry-Run: $DRY_RUN"

until docker info >/dev/null 2>&1; do
    log "WARN" "Docker-Daemon noch nicht erreichbar."
    date +%s > "$HEARTBEAT_FILE"
    sleep 5
done

remaining="$START_PERIOD"
while [ "$remaining" -gt 0 ]; do
    step=10
    if [ "$remaining" -lt "$step" ]; then
        step="$remaining"
    fi

    debug "Startphase: noch ${remaining}s"
    date +%s > "$HEARTBEAT_FILE"
    sleep "$step"
    remaining=$((remaining - step))
done

while :; do
    date +%s > "$HEARTBEAT_FILE"

    container_ids="$(
        docker ps \
            --quiet \
            --filter "label=${LABEL_KEY}=${LABEL_VALUE}" \
            2>/dev/null || true
    )"

    if [ -z "$container_ids" ]; then
        debug "Keine passenden laufenden Container gefunden."
    fi

    # Docker returns newline-separated container IDs; intentional splitting.
    # shellcheck disable=SC2086
    for container_id in $container_ids; do
        inspect="$(
            docker inspect \
                --format '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}|{{.Name}}' \
                "$container_id" \
                2>/dev/null || true
        )"

        if [ -z "$inspect" ]; then
            log "WARN" "Container $container_id konnte nicht gelesen werden."
            continue
        fi

        IFS='|' read -r status health name <<EOF
$inspect
EOF
        name="${name#/}"

        debug "Container=$name Status=$status Health=$health"

        if [ "$status" != "running" ]; then
            continue
        fi

        if [ "$health" = "none" ]; then
            debug "$name besitzt keinen Healthcheck."
            continue
        fi

        if [ "$health" != "unhealthy" ]; then
            continue
        fi

        timeout="$(
            docker inspect \
                --format '{{with index .Config.Labels "autoheal.stop.timeout"}}{{.}}{{end}}' \
                "$container_id" \
                2>/dev/null || true
        )"

        if ! is_uint "$timeout"; then
            timeout="$STOP_TIMEOUT"
        fi

        safe_name="$(printf '%s' "$name" | tr -c 'A-Za-z0-9_.-' '_')"
        event_file="$STATE_DIR/${safe_name}.events"
        temp_file="$event_file.tmp.$$"

        touch "$event_file"

        now="$(date +%s)"
        oldest_allowed=$((now - RESTART_WINDOW))

        awk -v minimum="$oldest_allowed" '
            $1 ~ /^[0-9]+$/ && $1 >= minimum { print $1 }
        ' "$event_file" > "$temp_file"
        mv "$temp_file" "$event_file"

        restart_count="$(wc -l < "$event_file" | tr -d '[:space:]')"
        last_restart="$(tail -n 1 "$event_file" 2>/dev/null || true)"

        if ! is_uint "$last_restart"; then
            last_restart=0
        fi

        seconds_since_restart=$((now - last_restart))

        if [ "$last_restart" -gt 0 ] && [ "$seconds_since_restart" -lt "$COOLDOWN" ]; then
            log "WARN" "$name ist unhealthy, aber noch im Cooldown (${seconds_since_restart}/${COOLDOWN}s)."
            continue
        fi

        if [ "$MAX_RESTARTS" -gt 0 ] && [ "$restart_count" -ge "$MAX_RESTARTS" ]; then
            log "ERROR" "$name bleibt unhealthy. Restart-Limit erreicht: ${restart_count}/${MAX_RESTARTS} im Zeitfenster."
            continue
        fi

        if [ "$DRY_RUN" = "true" ]; then
            log "WARN" "DRY-RUN: $name würde mit Stop-Timeout ${timeout}s neu gestartet."
            continue
        fi

        log "WARN" "$name ist unhealthy und wird neu gestartet. Stop-Timeout: ${timeout}s"

        if docker restart --timeout "$timeout" "$container_id" >/dev/null; then
            date +%s >> "$event_file"
            log "INFO" "$name wurde erfolgreich neu gestartet."
        else
            log "ERROR" "Neustart von $name ist fehlgeschlagen."
        fi
    done

    date +%s > "$HEARTBEAT_FILE"
    sleep "$INTERVAL"
done
