# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2026-07-24

### Stable release

- promoted the tested release candidate to the first stable version
- published fixed `1.0.0`, series `1.0` and `latest` image tags
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

## [0.1.0-rc1] - 2026-07-24

### Added

- Docker health monitoring through a configurable label
- controlled restart of `unhealthy` containers
- global startup delay and check interval
- per-container stop timeout through `autoheal.stop.timeout`
- dry-run mode
- persistent restart-event history
- configurable cooldown
- restart limit within a configurable time window
- built-in container healthcheck
- Alpine 3.24 based multi-architecture image
- GitHub Actions builds and Trivy security scans
- German and English documentation
