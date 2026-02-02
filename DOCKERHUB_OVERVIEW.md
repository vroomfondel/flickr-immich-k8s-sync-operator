[![black-lint](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/actions/workflows/checkblack.yml/badge.svg)](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/actions/workflows/checkblack.yml)
[![mypy and pytests](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/actions/workflows/mypynpytests.yml/badge.svg)](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/actions/workflows/mypynpytests.yml)
![Cumulative Clones](https://img.shields.io/endpoint?logo=github&url=https://gist.githubusercontent.com/vroomfondel/ba86ae83a5d1cfffce03ce36d30fa02d/raw/flickr-immich-k8s-sync-operator_somestuff_clone_count.json)

# flickr-immich-k8s-sync-operator

Kubernetes operator that watches per-user Flickr download Jobs in a namespace,
restarts failed Jobs after a configurable delay, and retrieves pod logs and exit
codes for failed Jobs before restarting them. Designed to run alongside
[Immich](https://immich.app/) (self-hosted photo management).

- **Source**: [GitHub](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator)
- **PyPI**: [flickr-immich-k8s-sync-operator](https://pypi.org/project/flickr-immich-k8s-sync-operator/)
- **License**: LGPLv3

## Features

- Monitors configured Kubernetes Jobs for failure conditions
- Retrieves pod logs and exit codes before restarting
- Configurable check interval and restart delay
- Clean signal handling (SIGTERM/SIGINT) for graceful container shutdown
- Structured logging via loguru

## Quick start

```bash
docker run --rm xomoxcc/flickr-immich-k8s-sync-operator:latest
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `LOGURU_LEVEL` | Log verbosity (`DEBUG`, `INFO`, `WARNING`, ...) | `DEBUG` |
| `NAMESPACE` | Namespace to watch | `flickr-downloader` |
| `JOB_NAMES` | Comma-separated Job names to monitor (**required**) | -- |
| `CHECK_INTERVAL` | Seconds between check cycles | `60` |
| `RESTART_DELAY` | Seconds to wait after failure before restart | `3600` |

## Kubernetes Deployment

The operator runs as a single-replica Deployment with a namespace-scoped ServiceAccount.
See the [README](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator#kubernetes-deployment) for full RBAC and Deployment manifests.

## Image details

- Base: `python:3.14-slim-trixie`
- Non-root user (`pythonuser`)
- Entrypoint: `tini --` with `flickr-immich-k8s-sync-operator` as default CMD
- Multi-arch: `linux/amd64`, `linux/arm64`