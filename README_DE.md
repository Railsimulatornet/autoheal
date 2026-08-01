# Autoheal – Deutsche Dokumentation

[Zur zweisprachigen Hauptdokumentation](README.md)

Autoheal überwacht Docker-Container mit einem Healthcheck und startet passend markierte Container kontrolliert neu, sobald sie den Zustand `unhealthy` erreichen.

## Hauptfunktionen

- Auswahl über `autoheal=true`
- Dry-Run-Modus
- konfigurierbare Startphase und Prüfintervalle
- individuelles Stop-Timeout über `autoheal.stop.timeout`
- Cooldown zwischen Neustarts
- maximales Neustartlimit innerhalb eines Zeitfensters
- persistente Ereignisdaten unter `/state`
- eigener Container-Healthcheck
- Multi-Arch-Images für AMD64 und ARM64

## Verwendung

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

volumes:
  autoheal_state:
```

Der zu überwachende Container benötigt einen funktionierenden Docker-Healthcheck und das Label:

```yaml
labels:
  autoheal: "true"
  autoheal.stop.timeout: "10"
```

## Schutz vor Neustartschleifen

Bei jedem erfolgreichen Autoheal-Neustart wird ein Unix-Zeitstempel in `/state/<container>.events` gespeichert. Vor einem weiteren Neustart prüft Autoheal:

1. ob der Cooldown bereits abgelaufen ist,
2. wie viele Ereignisse innerhalb von `AUTOHEAL_RESTART_WINDOW` liegen,
3. ob `AUTOHEAL_MAX_RESTARTS` erreicht wurde.

Mit `AUTOHEAL_MAX_RESTARTS=0` lässt sich nur das Limit deaktivieren. Der Cooldown bleibt davon unabhängig aktiv.

## Dry-Run

Für einen sicheren ersten Test:

```yaml
AUTOHEAL_DRY_RUN: "true"
AUTOHEAL_LOG_LEVEL: debug
```

Autoheal erkennt dann passende Container und protokolliert die vorgesehene Aktion, führt aber keinen Neustart aus.

## Image-Tags

- `latest` – Standardtag und aktuelle stabile Version
- `1.0.0` – fester stabiler Release

`latest` ist für die normale Installation vorgesehen. Für vollständig reproduzierbare Installationen kann stattdessen `1.0.0` verwendet werden.

## Sicherheit

Der Docker-Socket ermöglicht weitreichende Aktionen auf dem Docker-Host. Das Image und die Compose-Konfiguration dürfen deshalb nur von vertrauenswürdigen Administratoren geändert werden.

Weitere Hinweise stehen in [SECURITY.md](SECURITY.md).

## Lizenz

MIT License – Copyright (c) 2026 Roman Glos / Railsimulatornet
