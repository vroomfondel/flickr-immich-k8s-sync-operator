"""Job-restart operator — watches Kubernetes Jobs and restarts failed ones."""

from __future__ import annotations

import copy
import textwrap
import threading
from datetime import datetime, timezone

from kubernetes import client, config
from loguru import logger as glogger

from flickr_immich_k8s_sync_operator.config import OperatorConfig

# Labels auto-added by the Job controller that reference the old
# Job's UID — must be stripped before creating a new Job.
SERVER_MANAGED_LABELS: frozenset[str] = frozenset(
    {
        "controller-uid",
        "batch.kubernetes.io/controller-uid",
        "job-name",
        "batch.kubernetes.io/job-name",
    }
)


def build_manifest(job_dict: dict) -> dict:  # type: ignore[type-arg]
    """Build a clean Job manifest from a serialised ``V1Job`` dict.

    The input is expected to be the result of
    ``ApiClient().sanitize_for_serialization(job)`` or equivalent
    ``V1Job.to_dict()`` output.

    The returned manifest is safe to pass to
    ``create_namespaced_job`` — server-managed metadata, status, and
    controller labels on the pod template are removed.

    The *job_dict* is **not** mutated.
    """
    raw = copy.deepcopy(job_dict)

    template = raw["spec"]["template"]

    # Strip server-managed labels from pod template
    tmpl_labels = template.get("metadata", {}).get("labels", {})
    for label in SERVER_MANAGED_LABELS:
        tmpl_labels.pop(label, None)

    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": raw["metadata"]["name"],
            "namespace": raw["metadata"]["namespace"],
        },
        "spec": {
            "backoffLimit": raw["spec"]["backoffLimit"],
            "template": template,
        },
    }


class JobRestartOperator:
    """Watches a set of Kubernetes Jobs and restarts failed ones after a delay."""

    def __init__(self, cfg: OperatorConfig) -> None:
        config.load_incluster_config()
        self._batch_v1 = client.BatchV1Api()
        self._core_v1 = client.CoreV1Api()
        self._api_client = client.ApiClient()
        self._cfg = cfg
        self._cached_manifests: dict[str, dict] = {}  # type: ignore[type-arg]
        self._log = glogger.bind(classname=self.__class__.__name__)

    def run(self, shutdown_event: threading.Event) -> None:
        """Main operator loop — runs until *shutdown_event* is set."""
        self._log.info(
            "Operator started — watching {} job(s) in namespace '{}'",
            len(self._cfg.job_names),
            self._cfg.namespace,
        )
        while not shutdown_event.is_set():
            for job_name in self._cfg.job_names:
                if shutdown_event.is_set():
                    break
                self._check_job(job_name, shutdown_event)
            if not shutdown_event.is_set():
                self._log.info("Sleeping for {}s", self._cfg.check_interval)
                shutdown_event.wait(timeout=self._cfg.check_interval)

    def _check_job(self, job_name: str, shutdown_event: threading.Event) -> None:
        """Read a single Job and dispatch to the appropriate handler."""
        self._log.opt(raw=True).info("\n")
        self._log.info("Checking {}", job_name)
        try:
            job = self._batch_v1.read_namespaced_job(job_name, self._cfg.namespace)
            self._cached_manifests[job_name] = build_manifest(self._api_client.sanitize_for_serialization(job))

            conditions = job.status.conditions or []
            failed = any(c.type == "Failed" and c.status == "True" for c in conditions)

            if job.status.active:
                self._log.info("\t{} is running.", job_name)
            elif failed:
                fail_condition = next(c for c in conditions if c.type == "Failed" and c.status == "True")
                self._handle_failed_job(job_name, fail_condition.last_transition_time, shutdown_event)
            else:
                self._log.info("\t{} succeeded or still pending. No action needed.", job_name)
        except client.ApiException as exc:
            if exc.status == 404:
                self._log.info("\t{} not found. Nothing to do.", job_name)
            else:
                self._log.error("\tKubernetes API error for {}: {}", job_name, exc)
        except Exception:
            self._log.exception("\tUnexpected error for {}", job_name)

    def _handle_failed_job(
        self,
        job_name: str,
        failure_time: datetime,
        shutdown_event: threading.Event,
    ) -> None:
        """Log pod details and restart the Job if the restart delay has elapsed."""
        elapsed = (datetime.now(timezone.utc) - failure_time).total_seconds()

        self._log_pod_details(job_name)

        if elapsed >= self._cfg.restart_delay:
            self._log.info(
                "\t{} failed {:.0f}s ago (>= {}s). Deleting and recreating...",
                job_name,
                elapsed,
                self._cfg.restart_delay,
            )
            self._restart_job(job_name, shutdown_event)
        else:
            remaining = self._cfg.restart_delay - elapsed
            self._log.info(
                "\t{} failed {:.0f}s ago. Waiting {:.0f}s more before restart.",
                job_name,
                elapsed,
                remaining,
            )

    def _log_pod_details(self, job_name: str) -> None:
        """List pods for *job_name* and log exit codes + tail logs."""
        try:
            pods = self._core_v1.list_namespaced_pod(
                self._cfg.namespace,
                label_selector=f"job-name={job_name}",
            )
            for pod in pods.items:
                pod_name: str = pod.metadata.name
                exit_code = None
                reason = None
                for cs in pod.status.container_statuses or []:
                    if cs.state and cs.state.terminated:
                        exit_code = cs.state.terminated.exit_code
                        reason = cs.state.terminated.reason
                        break
                try:
                    tail = self._core_v1.read_namespaced_pod_log(
                        pod_name,
                        self._cfg.namespace,
                        tail_lines=2,
                    )
                except Exception:
                    tail = "<logs unavailable>"
                indented_tail = textwrap.indent(tail.strip(), "\t")
                self._log.info(
                    "\t{}: exit_code={}, reason={}, last log lines:\n{}",
                    pod_name,
                    exit_code,
                    reason,
                    indented_tail,
                )
        except Exception:
            self._log.warning("\tCould not retrieve pod details for {}", job_name)

    def _restart_job(self, job_name: str, shutdown_event: threading.Event) -> None:
        """Delete and recreate a Job from the cached manifest."""
        self._batch_v1.delete_namespaced_job(
            job_name,
            self._cfg.namespace,
            body=client.V1DeleteOptions(propagation_policy="Foreground"),
        )
        # Wait for Kubernetes to clean up resources (interruptible).
        if shutdown_event.wait(timeout=15):
            return
        self._batch_v1.create_namespaced_job(
            self._cfg.namespace,
            self._cached_manifests[job_name],
        )
        self._log.info("\t{} restarted successfully.", job_name)
