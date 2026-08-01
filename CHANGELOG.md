# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2026-07-24

### Stable release

- promoted the tested release candidate to the first stable version
- published `latest` as the standard image tag and `1.0.0` as the fixed release tag
- kept multi-architecture support for AMD64 and ARM64
- retained cooldown, persistent restart limits, dry-run mode and per-container stop timeouts
- updated GitHub, Docker Hub and Compose documentation for the stable release

### Verified before release

- healthy-container observation without restart
- real restart of an isolated unhealthy test container
- cooldown behavior
- persistent event counter
- restart-loop protection after reaching the configured limit
- published Docker Hub image dry-run against real healthy containers
- Trivy scan with no fixable critical or high findings
