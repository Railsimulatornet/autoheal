# Autoheal

Lightweight multi-architecture Docker health monitor with cooldown and restart-loop protection.

## Deutsch

Autoheal überwacht Container mit einem Docker-Healthcheck und startet passend markierte Container kontrolliert neu, wenn sie `unhealthy` werden.

### Funktionen

- Auswahl über ein konfigurierbares Label
- Dry-Run-Modus
- individuelles Stop-Timeout
- Cooldown zwischen Neustarts
- maximales Neustartlimit pro Zeitfenster
- persistente Neustart-Historie
- eigener Healthcheck
- Images für AMD64 und ARM64

### Beispiel

```yaml
services:
  autoheal:
    image: railsimulatornet/autoheal:1.0.0
    restart: unless-stopped
    environment:
      AUTOHEAL_CONTAINER_LABEL: autoheal
      AUTOHEAL_CONTAINER_LABEL_VALUE: "true"
      AUTOHEAL_INTERVAL: "30"
      AUTOHEAL_COOLDOWN: "300"
      AUTOHEAL_MAX_RESTARTS: "3"
      AUTOHEAL_RESTART_WINDOW: "1800"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - autoheal_state:/state

volumes:
  autoheal_state:
```

Zu überwachende Container benötigen einen Healthcheck und das Label `autoheal=true`.

### Image-Tags

- `1.0.0` – fester stabiler Release
- `1.0` – aktuellster Patchstand der 1.0-Reihe
- `latest` – aktuellste stabile Version

## English

Autoheal monitors containers with a Docker healthcheck and restarts selected containers in a controlled manner when they become `unhealthy`.

### Features

- configurable label selection
- dry-run mode
- per-container stop timeout
- cooldown between restarts
- maximum restart count per time window
- persistent restart history
- built-in healthcheck
- AMD64 and ARM64 images

### Image tags

- `1.0.0` – fixed stable release
- `1.0` – newest patch release in the 1.0 series
- `latest` – current stable release

### Security notice

Mounting the Docker socket gives the container extensive control over the Docker daemon and effectively the host. Use trusted images and fixed version tags.

Full documentation and source code:

**https://github.com/Railsimulatornet/autoheal**

## License

MIT License. Copyright (c) 2026 Roman Glos / Railsimulatornet.
