# Autoheal

[![Docker Image](https://github.com/Railsimulatornet/autoheal/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/Railsimulatornet/autoheal/actions/workflows/docker-publish.yml)
[![Security Scan](https://github.com/Railsimulatornet/autoheal/actions/workflows/security-scan.yml/badge.svg)](https://github.com/Railsimulatornet/autoheal/actions/workflows/security-scan.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Lightweight Docker health monitor with cooldown and restart-loop protection.

## Deutsch

### Was ist Autoheal?

Autoheal überwacht laufende Docker-Container mit einem Healthcheck. Sobald ein passend markierter Container den Zustand `unhealthy` erreicht, kann Autoheal ihn kontrolliert neu starten.

Im Unterschied zu einfachen Neustartschleifen enthält dieses Projekt zusätzliche Schutzmechanismen:

- Auswahl über ein frei konfigurierbares Docker-Label
- global konfigurierbare Startphase
- individuelles Stop-Timeout über das Label `autoheal.stop.timeout`
- Cooldown zwischen zwei Neustarts
- maximales Neustartlimit innerhalb eines Zeitfensters
- persistente Neustart-Historie unter `/state`
- Dry-Run-Modus ohne echte Neustarts
- eigener Container-Healthcheck
- verständliche Logs mit Begründung jeder Entscheidung
- Multi-Arch-Images für `linux/amd64` und `linux/arm64`
- automatisierte Shell-, Build- und Trivy-Prüfungen

### Schnellstart

```yaml
services:
  autoheal:
    image: railsimulatornet/autoheal:latest
    container_name: autoheal
    restart: unless-stopped
    environment:
      TZ: Europe/Berlin
      AUTOHEAL_CONTAINER_LABEL: autoheal
      AUTOHEAL_CONTAINER_LABEL_VALUE: "true"
      AUTOHEAL_INTERVAL: "30"
      AUTOHEAL_START_PERIOD: "120"
      AUTOHEAL_DEFAULT_STOP_TIMEOUT: "10"
      AUTOHEAL_COOLDOWN: "300"
      AUTOHEAL_MAX_RESTARTS: "3"
      AUTOHEAL_RESTART_WINDOW: "1800"
      AUTOHEAL_DRY_RUN: "false"
      AUTOHEAL_LOG_LEVEL: info
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - autoheal_state:/state

  example:
    image: nginx:alpine
    labels:
      autoheal: "true"
      autoheal.stop.timeout: "10"
    healthcheck:
      test: ["CMD", "wget", "--spider", "--quiet", "http://127.0.0.1/"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  autoheal_state:
```

Die vollständige Beispieldatei befindet sich unter [`examples/docker-compose.yml`](examples/docker-compose.yml).

### Konfiguration

| Variable | Standard | Bedeutung |
|---|---:|---|
| `AUTOHEAL_CONTAINER_LABEL` | `autoheal` | Name des Auswahl-Labels |
| `AUTOHEAL_CONTAINER_LABEL_VALUE` | `true` | Erwarteter Label-Wert |
| `AUTOHEAL_INTERVAL` | `30` | Prüfintervall in Sekunden |
| `AUTOHEAL_START_PERIOD` | `120` | Wartezeit nach dem Start von Autoheal |
| `AUTOHEAL_DEFAULT_STOP_TIMEOUT` | `10` | Standard-Timeout beim Neustart |
| `AUTOHEAL_COOLDOWN` | `300` | Mindestabstand zwischen Neustarts |
| `AUTOHEAL_MAX_RESTARTS` | `3` | Maximale Neustarts im Zeitfenster; `0` deaktiviert das Limit |
| `AUTOHEAL_RESTART_WINDOW` | `1800` | Zeitfenster für das Neustartlimit |
| `AUTOHEAL_DRY_RUN` | `false` | Nur protokollieren, nicht neu starten |
| `AUTOHEAL_LOG_LEVEL` | `info` | `info` oder `debug` |
| `AUTOHEAL_STATE_DIR` | `/state` | Ordner für persistente Ereignisdaten |
| `DOCKER_SOCK` | `/var/run/docker.sock` | Pfad zum Docker-Socket |

### Kompatibilität

Die häufig verwendeten Variablen `AUTOHEAL_CONTAINER_LABEL`, `AUTOHEAL_INTERVAL`, `AUTOHEAL_START_PERIOD` und `AUTOHEAL_DEFAULT_STOP_TIMEOUT` werden unterstützt.

Version 1.0.0 unterstützt noch keine Webhooks, Apprise-Benachrichtigungen oder benutzerdefinierten Post-Restart-Skripte.

### Sicherheitshinweis

Der eingebundene Docker-Socket gewährt dem Container weitreichenden Zugriff auf den Docker-Daemon und damit faktisch auf den Host. Verwende ausschließlich vertrauenswürdige Images und schütze den Container sowie seine Konfiguration vor unberechtigten Änderungen.

Ausführliche Hinweise stehen in [`SECURITY.md`](SECURITY.md).

### Image-Quellen und Tags

- Docker Hub: `railsimulatornet/autoheal`
- GitHub Container Registry: `ghcr.io/railsimulatornet/autoheal`
- Standardtag: `latest`
- fester Release: `1.0.0`

`latest` ist für die normale Installation vorgesehen. Für vollständig reproduzierbare Installationen kann stattdessen der feste Tag `1.0.0` verwendet werden.

### Copyright

Copyright (c) 2026 Roman Glos / Railsimulatornet

---

## English

### What is Autoheal?

Autoheal monitors running Docker containers that define a healthcheck. When a selected container reaches the `unhealthy` state, Autoheal can restart it in a controlled manner.

Additional safeguards prevent endless restart loops:

- selection through a configurable Docker label
- configurable global startup delay
- per-container stop timeout through `autoheal.stop.timeout`
- cooldown between restarts
- maximum restart count within a time window
- persistent restart history under `/state`
- dry-run mode without real restarts
- built-in container healthcheck
- clear logs explaining every decision
- multi-architecture images for `linux/amd64` and `linux/arm64`
- automated shell, build and Trivy checks

### Quick start

```yaml
services:
  autoheal:
    image: railsimulatornet/autoheal:latest
    container_name: autoheal
    restart: unless-stopped
    environment:
      TZ: Europe/Berlin
      AUTOHEAL_CONTAINER_LABEL: autoheal
      AUTOHEAL_CONTAINER_LABEL_VALUE: "true"
      AUTOHEAL_INTERVAL: "30"
      AUTOHEAL_START_PERIOD: "120"
      AUTOHEAL_DEFAULT_STOP_TIMEOUT: "10"
      AUTOHEAL_COOLDOWN: "300"
      AUTOHEAL_MAX_RESTARTS: "3"
      AUTOHEAL_RESTART_WINDOW: "1800"
      AUTOHEAL_DRY_RUN: "false"
      AUTOHEAL_LOG_LEVEL: info
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - autoheal_state:/state

  example:
    image: nginx:alpine
    labels:
      autoheal: "true"
      autoheal.stop.timeout: "10"
    healthcheck:
      test: ["CMD", "wget", "--spider", "--quiet", "http://127.0.0.1/"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  autoheal_state:
```

The complete example is available at [`examples/docker-compose.yml`](examples/docker-compose.yml).

### Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `AUTOHEAL_CONTAINER_LABEL` | `autoheal` | Selection label name |
| `AUTOHEAL_CONTAINER_LABEL_VALUE` | `true` | Required label value |
| `AUTOHEAL_INTERVAL` | `30` | Check interval in seconds |
| `AUTOHEAL_START_PERIOD` | `120` | Delay after Autoheal starts |
| `AUTOHEAL_DEFAULT_STOP_TIMEOUT` | `10` | Default restart timeout |
| `AUTOHEAL_COOLDOWN` | `300` | Minimum delay between restarts |
| `AUTOHEAL_MAX_RESTARTS` | `3` | Maximum restarts in the window; `0` disables the limit |
| `AUTOHEAL_RESTART_WINDOW` | `1800` | Restart-limit time window |
| `AUTOHEAL_DRY_RUN` | `false` | Log decisions without restarting |
| `AUTOHEAL_LOG_LEVEL` | `info` | `info` or `debug` |
| `AUTOHEAL_STATE_DIR` | `/state` | Persistent event directory |
| `DOCKER_SOCK` | `/var/run/docker.sock` | Docker socket path |

### Compatibility

The commonly used variables `AUTOHEAL_CONTAINER_LABEL`, `AUTOHEAL_INTERVAL`, `AUTOHEAL_START_PERIOD` and `AUTOHEAL_DEFAULT_STOP_TIMEOUT` are supported.

Version 1.0.0 does not yet support webhooks, Apprise notifications or custom post-restart scripts.

### Security notice

Mounting the Docker socket gives the container extensive control over the Docker daemon and effectively the host. Use only trusted images and protect the container and its configuration from unauthorized changes.

See [`SECURITY.md`](SECURITY.md) for details.

### Image sources and tags

- Docker Hub: `railsimulatornet/autoheal`
- GitHub Container Registry: `ghcr.io/railsimulatornet/autoheal`
- default tag: `latest`
- fixed release: `1.0.0`

`latest` is intended for normal installations. Use the fixed `1.0.0` tag instead when full reproducibility is required.

### Copyright

Copyright (c) 2026 Roman Glos / Railsimulatornet
