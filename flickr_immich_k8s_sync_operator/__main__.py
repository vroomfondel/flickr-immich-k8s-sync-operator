"""CLI entry point — signal handling, startup banner, and main loop."""

import signal
import sys
import threading

from loguru import logger as glogger

from flickr_immich_k8s_sync_operator import configure_logging, print_startup_banner
from flickr_immich_k8s_sync_operator.config import OperatorConfig
from flickr_immich_k8s_sync_operator.operator import JobRestartOperator

configure_logging()
glogger.enable("flickr_immich_k8s_sync_operator")

shutdown_event = threading.Event()


def _signal_handler(signum: int, frame: object) -> None:
    """Handle SIGTERM/SIGINT by setting the module-level shutdown event.

    Args:
        signum: Signal number received from the OS.
        frame: Current stack frame (unused).
    """
    signame = signal.Signals(signum).name
    glogger.info(f"Received {signame} — shutting down...")
    shutdown_event.set()


def main() -> None:
    """Run the operator.

    Registers signal handlers, prints a startup banner with version and
    configuration, initialises the Kubernetes client, and enters the
    operator's main loop.
    """
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    try:
        cfg = OperatorConfig.from_env()
        print_startup_banner(cfg)
    except ValueError as exc:
        glogger.error("Configuration error: {}", exc)
        sys.exit(1)

    try:
        operator = JobRestartOperator(cfg)
    except Exception as exc:
        glogger.error("Failed to initialise Kubernetes clients: {}", exc)
        sys.exit(1)

    operator.run(shutdown_event)

    glogger.info("flickr-immich-k8s-sync-operator shut down cleanly")


if __name__ == "__main__":
    main()
