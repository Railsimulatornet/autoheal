# Autoheal

[![Docker Image](https://github.com/Railsimulatornet/autoheal/actions/workflows/docker-publish.yml/badge.svg?branch=main)](https://github.com/Railsimulatornet/autoheal/actions/workflows/docker-publish.yml)
[![Security Scan](https://github.com/Railsimulatornet/autoheal/actions/workflows/security-scan.yml/badge.svg?branch=main)](https://github.com/Railsimulatornet/autoheal/actions/workflows/security-scan.yml)
[![CodeQL](https://github.com/Railsimulatornet/autoheal/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/Railsimulatornet/autoheal/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Deutsch](#deutsch) · [English](#english)

## Deutsch

Autoheal überwacht laufende Docker-Container mit einem Healthcheck. Erreicht ein passend markierter Container den Zustand `unhealthy`, kann Autoheal ihn kontrolliert neu starten. Cooldown und Neustartlimit begrenzen wiederholte Neustarts.

### Funktionen

- Container über ein frei wählbares Label und dessen Wert auswählen
- Startphase, Prüfintervall und Stop-Timeout einstellen
- Pro Container Cooldown und Neustartlimit in einem Zeitfenster anwenden
- Neustart-Historie unter `/state` dauerhaft speichern
- Entscheidungen mit Dry-Run und Debug-Logs nachvollziehen
- Eigener Container-Healthcheck und Images für `linux/amd64` sowie `linux/arm64`
- Automatische Shell-, Laufzeit-, Build- und Trivy-Prüfungen

### Voraussetzungen

- Docker auf einem Linux-Host mit AMD64 oder ARM64
- Docker Compose oder eine entsprechende Projektverwaltung wie die UGOS-Docker-App
- Ein funktionierender Docker-Healthcheck und das passende Auswahl-Label am überwachten Container
- Zugriff auf den Docker-Socket und ein dauerhaft eingebundener Ordner oder ein Volume für `/state`

Container ohne Healthcheck oder ohne passendes Label werden nicht neu gestartet. Die Startphase gilt nach dem Start von Autoheal; sie ersetzt nicht die Startphase im Healthcheck des überwachten Containers.

### Schnellstart

Übernimm die [vollständige Beispieldatei](examples/docker-compose.yml) in dein Docker-Projekt. Das Beispiel enthält Autoheal und einen Nginx-Container mit Healthcheck:

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
    restart: unless-stopped
    labels:
      autoheal: "true"
      autoheal.stop.timeout: "10"
    healthcheck:
      test: ["CMD", "wget", "--spider", "--quiet", "http://127.0.0.1/"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 20s

volumes:
  autoheal_state:
```

Speichere die Konfiguration als `docker-compose.yml`. Starte sie aus dem Projektordner:

```bash
docker compose up -d
docker compose logs -f autoheal
```

Für eigene Dienste übernimmst du die Labels in deren Service-Konfiguration und verwendest einen Healthcheck, der zum jeweiligen Dienst passt.

### Konfiguration

Diese Werte werden im [Hauptskript](autoheal.sh) verwendet. Zeitangaben sind in Sekunden, sofern nicht anders angegeben.

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `AUTOHEAL_CONTAINER_LABEL` | `autoheal` | Name des Auswahl-Labels |
| `AUTOHEAL_CONTAINER_LABEL_VALUE` | `true` | Erwarteter Label-Wert |
| `AUTOHEAL_INTERVAL` | `30` | Prüfintervall, mindestens `1` |
| `AUTOHEAL_START_PERIOD` | `120` | Wartezeit nach dem Start von Autoheal |
| `AUTOHEAL_DEFAULT_STOP_TIMEOUT` | `10` | Standard-Stop-Timeout beim Neustart |
| `AUTOHEAL_COOLDOWN` | `300` | Mindestabstand zwischen Neustarts desselben Containers |
| `AUTOHEAL_MAX_RESTARTS` | `3` | Maximale Anzahl im Zeitfenster; `0` deaktiviert nur dieses Limit |
| `AUTOHEAL_RESTART_WINDOW` | `1800` | Zeitfenster für das Neustartlimit |
| `AUTOHEAL_DRY_RUN` | `false` | Mit `true` nur protokollieren |
| `AUTOHEAL_LOG_LEVEL` | `info` | `info` oder `debug` |
| `AUTOHEAL_STATE_DIR` | `/state` | Ordner für persistente Ereignisdaten |
| `DOCKER_SOCK` | `/var/run/docker.sock` | Pfad zum Docker-Socket im Container |

Das Label `autoheal.stop.timeout` am überwachten Container überschreibt dessen Stop-Timeout. Die übrigen Werte aus der Tabelle werden am Autoheal-Dienst gesetzt.

#### Neustartlimit und persistente Daten

Nach einem erfolgreichen Neustart speichert Autoheal einen Zeitstempel in einer Ereignisdatei unter `/state`. Vor dem nächsten Neustart prüft es den Cooldown und die Zahl der Ereignisse innerhalb von `AUTOHEAL_RESTART_WINDOW`.

Mit `AUTOHEAL_MAX_RESTARTS=0` wird nur das Anzahl-Limit deaktiviert. Der Cooldown bleibt aktiv. Behalte das eingebundene State-Volume auch beim Neuerstellen des Autoheal-Containers bei.

#### Dry-Run

Für einen ersten Test setzt du diese Werte unter `environment:` am Autoheal-Dienst:

```yaml
AUTOHEAL_DRY_RUN: "true"
AUTOHEAL_LOG_LEVEL: debug
```

Autoheal protokolliert dann die geplanten Aktionen und startet keine Container neu. Setze `AUTOHEAL_DRY_RUN` für den normalen Betrieb wieder auf `"false"` und erstelle den Dienst neu.

### Aktualisierung

Für den Autoheal-Dienst aus dem Beispiel, im vorhandenen Projektordner:

```bash
docker compose pull autoheal
docker compose up -d autoheal
docker compose logs -f autoheal
```

In UGOS kannst du das Projekt über **Neu bereitstellen** aktualisieren und **Das neueste Image abrufen** aktivieren. Verwende bei SSH-Aufrufen den bestehenden Compose-Projektnamen, bei Bedarf mit `docker compose -p NAME`.

Behalte deine Compose-Einstellungen und die Daten unter `/state`. Ein neues Image in der Registry aktualisiert den laufenden Container erst nach dem Abruf und Neuerstellen.

#### Image-Quellen und Tags

| Quelle | Image |
| --- | --- |
| Docker Hub | `railsimulatornet/autoheal` |
| GitHub Container Registry | `ghcr.io/railsimulatornet/autoheal` |

| Tag | Bedeutung |
| --- | --- |
| `latest` | Standardtag und aktueller geprüfter Build |
| `1.0.1` | Fester Release-Stand |
| `1.0.1-build.20261018.42.1` | Beispiel eines Wartungsbuilds mit Datum, Lauf- und Wiederholungsnummer |

`latest` wird wöchentlich frisch gebaut. Beide Architekturen werden geprüft, bevor dasselbe Image auf Docker Hub und GHCR veröffentlicht wird. Fehlgeschlagene Tests oder Sicherheitsscans blockieren die Veröffentlichung. Feste Versionstags werden bei Wartungsbuilds nicht überschrieben; die Commit-Zuordnung bleibt in den Image-Metadaten erhalten.

### Kompatibilität und Sicherheit

Die häufig verwendeten Variablen `AUTOHEAL_CONTAINER_LABEL`, `AUTOHEAL_INTERVAL`, `AUTOHEAL_START_PERIOD` und `AUTOHEAL_DEFAULT_STOP_TIMEOUT` werden unterstützt. Version **1.0.1** bietet keine Webhooks, Apprise-Benachrichtigungen oder eigenen Post-Restart-Skripte.

Der Docker-Socket ermöglicht weitreichende Kontrolle über Docker und damit faktisch über den Host. Verwende vertrauenswürdige Images und schütze den Container sowie seine Konfiguration vor unberechtigten Änderungen. Weitere Hinweise stehen in [SECURITY.md](SECURITY.md).

### Projektstruktur

| Pfad | Inhalt |
| --- | --- |
| `autoheal.sh` | Auswahl, Prüfungen und kontrollierte Neustarts |
| `healthcheck.sh` | Healthcheck des Autoheal-Containers |
| `Dockerfile` | Build-Quelle des Images |
| `examples/docker-compose.yml` | Vollständiges Compose-Beispiel |
| `VERSION` | Anwendungsversion |

### Dokumentation

- [Compose-Beispiel](examples/docker-compose.yml)
- [Sicherheitshinweise](SECURITY.md)
- [Änderungsverlauf](CHANGELOG.md)
- [Releases](https://github.com/Railsimulatornet/autoheal/releases)

### Lizenz

[MIT License](LICENSE) · Copyright (c) 2026 Roman Glos / Railsimulatornet.

## English

Autoheal monitors running Docker containers with a healthcheck. When a selected container becomes `unhealthy`, Autoheal can restart it in a controlled manner. A cooldown and restart limit restrict repeated restarts.

### Features

- Select containers through a configurable label and value
- Configure the startup delay, check interval and stop timeout
- Apply a cooldown and restart limit per container within a time window
- Persist restart history under `/state`
- Inspect decisions through dry-run mode and debug logs
- Built-in container healthcheck and images for `linux/amd64` and `linux/arm64`
- Automated shell, runtime, build and Trivy checks

### Requirements

- Docker on a Linux AMD64 or ARM64 host
- Docker Compose or a project manager such as the UGOS Docker app
- A working Docker healthcheck and the matching selection label on each monitored container
- Access to the Docker socket and a persistent directory or volume mounted at `/state`

Containers without a healthcheck or matching label are not restarted. The startup delay applies after Autoheal starts; it does not replace the healthcheck start period of the monitored container.

### Quick start

Copy the [complete example](examples/docker-compose.yml) into your Docker project. It includes Autoheal and an Nginx container with a healthcheck:

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
    restart: unless-stopped
    labels:
      autoheal: "true"
      autoheal.stop.timeout: "10"
    healthcheck:
      test: ["CMD", "wget", "--spider", "--quiet", "http://127.0.0.1/"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 20s

volumes:
  autoheal_state:
```

Save the configuration as `docker-compose.yml`. Start it from the project directory:

```bash
docker compose up -d
docker compose logs -f autoheal
```

For your own services, add the labels to their service configuration and use a healthcheck appropriate for each service.

### Configuration

These values are used by the [main script](autoheal.sh). Times are in seconds unless stated otherwise.

| Variable | Default | Purpose |
| --- | --- | --- |
| `AUTOHEAL_CONTAINER_LABEL` | `autoheal` | Selection label name |
| `AUTOHEAL_CONTAINER_LABEL_VALUE` | `true` | Required label value |
| `AUTOHEAL_INTERVAL` | `30` | Check interval, minimum `1` |
| `AUTOHEAL_START_PERIOD` | `120` | Delay after Autoheal starts |
| `AUTOHEAL_DEFAULT_STOP_TIMEOUT` | `10` | Default stop timeout when restarting |
| `AUTOHEAL_COOLDOWN` | `300` | Minimum interval between restarts of the same container |
| `AUTOHEAL_MAX_RESTARTS` | `3` | Maximum count within the window; `0` disables only this limit |
| `AUTOHEAL_RESTART_WINDOW` | `1800` | Restart-limit time window |
| `AUTOHEAL_DRY_RUN` | `false` | Set to `true` to log actions only |
| `AUTOHEAL_LOG_LEVEL` | `info` | `info` or `debug` |
| `AUTOHEAL_STATE_DIR` | `/state` | Persistent event directory |
| `DOCKER_SOCK` | `/var/run/docker.sock` | Docker socket path inside the container |

The `autoheal.stop.timeout` label on a monitored container overrides its stop timeout. Set the other values from the table on the Autoheal service.

#### Restart limit and persistent data

After a successful restart, Autoheal saves a timestamp in an event file under `/state`. Before the next restart, it checks the cooldown and the number of events within `AUTOHEAL_RESTART_WINDOW`.

Setting `AUTOHEAL_MAX_RESTARTS=0` disables only the count limit. The cooldown remains active. Keep the mounted state volume when recreating the Autoheal container.

#### Dry-run mode

For an initial test, set these values under `environment:` on the Autoheal service:

```yaml
AUTOHEAL_DRY_RUN: "true"
AUTOHEAL_LOG_LEVEL: debug
```

Autoheal then logs planned actions without restarting containers. For normal operation, set `AUTOHEAL_DRY_RUN` back to `"false"` and recreate the service.

### Updating

For the example Autoheal service, run from the existing project directory:

```bash
docker compose pull autoheal
docker compose up -d autoheal
docker compose logs -f autoheal
```

In UGOS, redeploy the project and enable **Download the latest image**. For SSH commands, use the existing Compose project name, adding `docker compose -p NAME` when needed.

Keep your Compose settings and data under `/state`. A new registry image updates the running container only after pulling it and recreating the service.

#### Image sources and tags

| Registry | Image |
| --- | --- |
| Docker Hub | `railsimulatornet/autoheal` |
| GitHub Container Registry | `ghcr.io/railsimulatornet/autoheal` |

| Tag | Meaning |
| --- | --- |
| `latest` | Default tag and current verified build |
| `1.0.1` | Fixed release |
| `1.0.1-build.20261018.42.1` | Example maintenance build with date, run number and attempt number |

`latest` is rebuilt weekly. Both architectures are checked before the same image is published to Docker Hub and GHCR. Failed tests or security scans block publication. Maintenance builds do not overwrite fixed version tags; source commit information remains in the image metadata.

### Compatibility and security

The commonly used variables `AUTOHEAL_CONTAINER_LABEL`, `AUTOHEAL_INTERVAL`, `AUTOHEAL_START_PERIOD` and `AUTOHEAL_DEFAULT_STOP_TIMEOUT` are supported. Version **1.0.1** does not provide webhooks, Apprise notifications or custom post-restart scripts.

The Docker socket gives the container extensive control over Docker and effectively the host. Use trusted images and protect the container and its configuration from unauthorized changes. See [SECURITY.md](SECURITY.md) for details.

### Project structure

| Path | Contents |
| --- | --- |
| `autoheal.sh` | Selection, checks and controlled restarts |
| `healthcheck.sh` | Autoheal container healthcheck |
| `Dockerfile` | Image build source |
| `examples/docker-compose.yml` | Complete Compose example |
| `VERSION` | Application version |

### Documentation

- [Compose example](examples/docker-compose.yml)
- [Security guidance](SECURITY.md)
- [Changelog](CHANGELOG.md)
- [Releases](https://github.com/Railsimulatornet/autoheal/releases)

### License

[MIT License](LICENSE) · Copyright (c) 2026 Roman Glos / Railsimulatornet.
