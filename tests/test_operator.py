"""Tests for :func:`flickr_immich_k8s_sync_operator.operator.build_manifest`."""

import copy

import pytest

from flickr_immich_k8s_sync_operator.operator import SERVER_MANAGED_LABELS, build_manifest


def _sample_job_dict() -> dict:  # type: ignore[type-arg]
    """Return a realistic serialised V1Job dict."""
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": "flickr-downloader-alice",
            "namespace": "flickr-downloader",
            "uid": "abc-123",
            "resourceVersion": "999",
            "creationTimestamp": "2025-01-01T00:00:00Z",
            "managedFields": [{"manager": "kube-controller-manager"}],
            "labels": {"app": "flickr"},
        },
        "spec": {
            "backoffLimit": 3,
            "template": {
                "metadata": {
                    "labels": {
                        "app": "flickr",
                        "controller-uid": "abc-123",
                        "batch.kubernetes.io/controller-uid": "abc-123",
                        "job-name": "flickr-downloader-alice",
                        "batch.kubernetes.io/job-name": "flickr-downloader-alice",
                    },
                },
                "spec": {
                    "containers": [
                        {
                            "name": "downloader",
                            "image": "flickr-dl:latest",
                        }
                    ],
                    "restartPolicy": "Never",
                },
            },
        },
        "status": {
            "conditions": [{"type": "Failed", "status": "True"}],
        },
    }


class TestBuildManifest:
    """Tests for :func:`build_manifest`."""

    def test_removes_status(self) -> None:
        result = build_manifest(_sample_job_dict())
        assert "status" not in result

    def test_removes_server_metadata(self) -> None:
        result = build_manifest(_sample_job_dict())
        meta = result["metadata"]
        assert "uid" not in meta
        assert "resourceVersion" not in meta
        assert "creationTimestamp" not in meta
        assert "managedFields" not in meta

    def test_strips_server_managed_labels(self) -> None:
        result = build_manifest(_sample_job_dict())
        tmpl_labels = result["spec"]["template"]["metadata"]["labels"]
        for label in SERVER_MANAGED_LABELS:
            assert label not in tmpl_labels

    def test_preserves_user_labels(self) -> None:
        result = build_manifest(_sample_job_dict())
        tmpl_labels = result["spec"]["template"]["metadata"]["labels"]
        assert tmpl_labels["app"] == "flickr"

    def test_does_not_mutate_input(self) -> None:
        original = _sample_job_dict()
        frozen = copy.deepcopy(original)
        build_manifest(original)
        assert original == frozen

    def test_handles_missing_template_labels(self) -> None:
        job = _sample_job_dict()
        del job["spec"]["template"]["metadata"]["labels"]
        result = build_manifest(job)
        # Should not raise and template metadata should still exist
        assert result["spec"]["template"]["metadata"] == {}

    def test_preserves_name_and_namespace(self) -> None:
        result = build_manifest(_sample_job_dict())
        assert result["metadata"]["name"] == "flickr-downloader-alice"
        assert result["metadata"]["namespace"] == "flickr-downloader"

    def test_preserves_backoff_limit(self) -> None:
        result = build_manifest(_sample_job_dict())
        assert result["spec"]["backoffLimit"] == 3

    def test_preserves_template_spec(self) -> None:
        result = build_manifest(_sample_job_dict())
        containers = result["spec"]["template"]["spec"]["containers"]
        assert len(containers) == 1
        assert containers[0]["name"] == "downloader"
