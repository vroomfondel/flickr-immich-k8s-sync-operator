[![black-lint](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/actions/workflows/checkblack.yml/badge.svg)](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/actions/workflows/checkblack.yml)
[![mypy and pytests](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/actions/workflows/mypynpytests.yml/badge.svg)](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/actions/workflows/mypynpytests.yml)
![Cumulative Clones](https://img.shields.io/endpoint?logo=github&url=https://gist.githubusercontent.com/vroomfondel/ba86ae83a5d1cfffce03ce36d30fa02d/raw/flickr-immich-k8s-sync-operator_somestuff_clone_count.json)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/flickr-immich-k8s-sync-operator?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=PyPi+Downloads)](https://pepy.tech/projects/flickr-immich-k8s-sync-operator)

[![Gemini_Generated_Image_gwjk7ggwjk7ggwjk_250x250.png](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator/raw/main/Gemini_Generated_Image_gwjk7ggwjk7ggwjk_250x250.png)](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator)

# flickr-immich-k8s-sync-operator

Kubernetes operator that watches per-user Flickr download Jobs in a namespace,
restarts failed Jobs after a configurable delay, and retrieves pod logs and exit
codes for failed Jobs before restarting them. Designed to run alongside
[Immich](https://immich.app/) (self-hosted photo management).

## Screenshots

![Operator startup with configuration overview](https://raw.githubusercontent.com/vroomfondel/flickr-immich-k8s-sync-operator/main/Bildschirmfoto_2026-02-16_19-51-45_blurred.png)

![Operator monitoring jobs across multiple check cycles](https://raw.githubusercontent.com/vroomfondel/flickr-immich-k8s-sync-operator/main/Bildschirmfoto_2026-02-16_19-52-07_blurred.png)

![Operator detecting failures and scheduling restarts](https://raw.githubusercontent.com/vroomfondel/flickr-immich-k8s-sync-operator/main/Bildschirmfoto_2026-02-02_18-43-40_blurred.png)

- **Source**: [GitHub](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator)
- **PyPI**: [flickr-immich-k8s-sync-operator](https://pypi.org/project/flickr-immich-k8s-sync-operator/)
- **License**: LGPLv3

## Features

- Monitors configured Kubernetes Jobs for failure conditions
- Retrieves pod logs and exit codes before restarting
- Configurable check interval and restart delay
- Clean signal handling (SIGTERM/SIGINT) for graceful container shutdown
- OOMKilled-aware restart logic — skips the restart delay when pods are killed by OOM
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
| `SKIP_DELAY_ON_OOM` | Skip restart delay when failure reason is `OOMKilled` | `false` |

## Kubernetes Deployment

The operator runs as a single-replica Deployment with a namespace-scoped ServiceAccount.
See the [README](https://github.com/vroomfondel/flickr-immich-k8s-sync-operator#kubernetes-deployment) for full RBAC and Deployment manifests.

## Image details

- Base: `python:3.14-slim-trixie`
- Non-root user (`pythonuser`)
- Entrypoint: `tini --` with `flickr-immich-k8s-sync-operator` as default CMD
- Multi-arch: `linux/amd64`, `linux/arm64`