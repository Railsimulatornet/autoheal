FROM alpine:3.24

ARG VERSION=dev

LABEL org.opencontainers.image.title="Autoheal"
LABEL org.opencontainers.image.description="Lightweight Docker health monitor with cooldown and restart-loop protection"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.source="https://github.com/Railsimulatornet/autoheal"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="Railsimulatornet"

RUN set -eux; \
    apk update; \
    apk upgrade --no-cache; \
    apk add --no-cache \
        ca-certificates \
        docker-cli \
        tini \
        tzdata; \
    mkdir -p /state; \
    rm -rf /var/cache/apk/*

COPY autoheal.sh /usr/local/bin/autoheal.sh
COPY healthcheck.sh /usr/local/bin/healthcheck.sh

RUN chmod 0755 \
        /usr/local/bin/autoheal.sh \
        /usr/local/bin/healthcheck.sh

ENV AUTOHEAL_CONTAINER_LABEL=autoheal \
    AUTOHEAL_CONTAINER_LABEL_VALUE=true \
    AUTOHEAL_INTERVAL=30 \
    AUTOHEAL_START_PERIOD=120 \
    AUTOHEAL_DEFAULT_STOP_TIMEOUT=10 \
    AUTOHEAL_COOLDOWN=300 \
    AUTOHEAL_MAX_RESTARTS=3 \
    AUTOHEAL_RESTART_WINDOW=1800 \
    AUTOHEAL_DRY_RUN=false \
    AUTOHEAL_LOG_LEVEL=info \
    AUTOHEAL_STATE_DIR=/state \
    AUTOHEAL_HEARTBEAT_FILE=/tmp/autoheal-heartbeat \
    DOCKER_SOCK=/var/run/docker.sock \
    TZ=UTC

VOLUME ["/state"]

ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/autoheal.sh"]

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=150s \
    --retries=3 \
    CMD ["/usr/local/bin/healthcheck.sh"]
