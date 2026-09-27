## Deutsch

### Autoheal v1.0.1

Dieses Update verbessert die Sicherheit und die automatische Pflege der Docker-Images.

- Vor der Veröffentlichung werden jetzt die Images für AMD64 und ARM64 auf behebbare schwere und kritische Sicherheitslücken geprüft.
- Docker Hub und die GitHub Container Registry erhalten dasselbe geprüfte Image.
- `latest` wird einmal pro Woche frisch gebaut und nur nach bestandenen Prüfungen aktualisiert.
- Wartungsbuilds erhalten verständliche Tags mit Version und Datum. Feste Release-Tags bleiben unverändert.

An der Überwachung, den Neustartregeln und deiner Konfiguration ändert sich nichts.

**Aktualisierung:** Bestehende Nutzer von `latest` können ihr Projekt in der UGOS-Docker-App neu bereitstellen und dabei **Das neueste Image abrufen** aktivieren. Wer einen festen Versionstag verwendet, kann auf `railsimulatornet/autoheal:1.0.1` wechseln. Die eigene Compose-Konfiguration und die Daten unter `/state` bitte beibehalten.

Beide Image-Quellen bleiben bestehen: `railsimulatornet/autoheal` und `ghcr.io/railsimulatornet/autoheal`.

---

## English

### Autoheal v1.0.1

This update improves Docker image security and automated maintenance.

- Both AMD64 and ARM64 images are now checked for fixable high and critical vulnerabilities before publication.
- Docker Hub and GitHub Container Registry receive the same verified image.
- `latest` is rebuilt weekly and updated only after all checks pass.
- Maintenance builds use readable version-and-date tags. Fixed release tags remain unchanged.

Monitoring, restart rules and configuration remain unchanged.

**Updating:** Existing `latest` users can redeploy their project in the UGOS Docker app with **Download the latest image** enabled. Users of a fixed version tag can switch to `railsimulatornet/autoheal:1.0.1`. Keep the existing Compose configuration and data under `/state`.

Both image sources remain available: `railsimulatornet/autoheal` and `ghcr.io/railsimulatornet/autoheal`.
