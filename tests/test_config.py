"""Tests for :mod:`flickr_immich_k8s_sync_operator.config`."""

import dataclasses

import pytest

from flickr_immich_k8s_sync_operator.config import OperatorConfig


class TestOperatorConfigFromEnv:
    """Tests for :meth:`OperatorConfig.from_env`."""

    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOB_NAMES", "job-a,job-b")
        monkeypatch.delenv("NAMESPACE", raising=False)
        monkeypatch.delenv("CHECK_INTERVAL", raising=False)
        monkeypatch.delenv("RESTART_DELAY", raising=False)
        monkeypatch.delenv("SKIP_DELAY_ON_OOM", raising=False)

        cfg = OperatorConfig.from_env()

        assert cfg.namespace == "flickr-downloader"
        assert cfg.job_names == ["job-a", "job-b"]
        assert cfg.check_interval == 60
        assert cfg.restart_delay == 3600
        assert cfg.skip_delay_on_oom is False

    def test_custom_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NAMESPACE", "  custom-ns  ")
        monkeypatch.setenv("JOB_NAMES", " job-x , job-y , job-z ")
        monkeypatch.setenv("CHECK_INTERVAL", "30")
        monkeypatch.setenv("RESTART_DELAY", "120")
        monkeypatch.setenv("SKIP_DELAY_ON_OOM", "true")

        cfg = OperatorConfig.from_env()

        assert cfg.namespace == "custom-ns"
        assert cfg.job_names == ["job-x", "job-y", "job-z"]
        assert cfg.check_interval == 30
        assert cfg.restart_delay == 120
        assert cfg.skip_delay_on_oom is True

    def test_missing_job_names_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JOB_NAMES", raising=False)

        with pytest.raises(ValueError, match="JOB_NAMES"):
            OperatorConfig.from_env()

    def test_empty_job_names_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOB_NAMES", "")

        with pytest.raises(ValueError, match="JOB_NAMES"):
            OperatorConfig.from_env()

    def test_whitespace_only_job_names_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOB_NAMES", "  ,  ,  ")

        with pytest.raises(ValueError, match="JOB_NAMES"):
            OperatorConfig.from_env()

    def test_single_job_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOB_NAMES", "only-one")
        monkeypatch.delenv("NAMESPACE", raising=False)

        cfg = OperatorConfig.from_env()

        assert cfg.job_names == ["only-one"]

    def test_frozen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOB_NAMES", "job-a")

        cfg = OperatorConfig.from_env()

        with pytest.raises(dataclasses.FrozenInstanceError):
            cfg.namespace = "nope"  # type: ignore[misc]

    @pytest.mark.parametrize(
        "env_value, expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("  true  ", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("1", False),
            ("yes", False),
            ("", False),
        ],
    )
    def test_skip_delay_on_oom_parsing(self, monkeypatch: pytest.MonkeyPatch, env_value: str, expected: bool) -> None:
        monkeypatch.setenv("JOB_NAMES", "job-a")
        monkeypatch.setenv("SKIP_DELAY_ON_OOM", env_value)

        cfg = OperatorConfig.from_env()

        assert cfg.skip_delay_on_oom is expected
