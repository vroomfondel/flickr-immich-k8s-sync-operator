"""Operator configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OperatorConfig:
    """Immutable configuration for the Job-restart operator.

    All values are sourced from environment variables via :meth:`from_env`.
    """

    namespace: str
    job_names: list[str]
    check_interval: int
    restart_delay: int
    skip_delay_on_oom: bool

    @classmethod
    def from_env(cls) -> OperatorConfig:
        """Build an :class:`OperatorConfig` from environment variables.

        Environment variables
        ---------------------
        NAMESPACE : str, optional
            Kubernetes namespace to watch (default ``"flickr-downloader"``).
        JOB_NAMES : str, **required**
            Comma-separated list of Job names to monitor.
        CHECK_INTERVAL : str, optional
            Seconds between check cycles (default ``60``).
        RESTART_DELAY : str, optional
            Seconds after failure before a Job is restarted (default ``3600``).
        SKIP_DELAY_ON_OOM : str, optional
            If ``"true"`` (case-insensitive), skip the restart delay when the
            failure reason is ``OOMKilled`` (default ``"false"``).

        Raises
        ------
        ValueError
            If ``JOB_NAMES`` is missing or contains no non-empty entries.
        """
        raw_job_names = os.environ.get("JOB_NAMES", "")
        job_names = [name.strip() for name in raw_job_names.split(",") if name.strip()]
        if not job_names:
            raise ValueError("JOB_NAMES environment variable is required and must contain at least one job name")

        return cls(
            namespace=os.environ.get("NAMESPACE", "flickr-downloader").strip(),
            job_names=job_names,
            check_interval=int(os.environ.get("CHECK_INTERVAL", "60")),
            restart_delay=int(os.environ.get("RESTART_DELAY", "3600")),
            skip_delay_on_oom=os.environ.get("SKIP_DELAY_ON_OOM", "false").strip().lower() == "true",
        )
