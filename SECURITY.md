# Security Policy

## Supported versions

During the release-candidate phase, security fixes are applied to the newest `0.1.x` release candidate. Older test images and superseded release candidates may no longer receive fixes.

Stable-version support will be documented when the first stable release is published.

## Reporting a vulnerability

Please use GitHub's private **Report a vulnerability** function in the Security tab of this repository whenever it is available.

Do not publish credentials, access tokens, private container metadata, host paths or working exploit details in a public issue. Public issues are suitable only for non-sensitive hardening suggestions or already-public dependency advisories.

A report should include:

- affected Autoheal version or image digest
- affected architecture
- a concise description of the issue
- reproducible steps that do not expose unrelated systems
- expected and observed behavior
- possible mitigation, when known

## Docker socket warning

Autoheal needs access to the Docker API to inspect and restart containers. Mounting `/var/run/docker.sock` gives the container extensive control over the Docker daemon and effectively the host.

Use only trusted images, pin a fixed version in production, restrict who can modify the Compose project, and protect the persistent state directory from unauthorized changes.

## Automated checks

The repository performs shell syntax checks, image builds and Trivy scans for fixable `CRITICAL` and `HIGH` findings. Automated scans reduce risk but do not replace review of the source code, container permissions and deployment environment.
