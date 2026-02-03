import signal
import sys
import threading
from dataclasses import fields

from loguru import logger as glogger
from tabulate import tabulate

from flickr_immich_k8s_sync_operator import __version__, configure_logging
from flickr_immich_k8s_sync_operator.config import OperatorConfig
from flickr_immich_k8s_sync_operator.operator import JobRestartOperator

configure_logging()
glogger.enable("flickr_immich_k8s_sync_operator")

shutdown_event = threading.Event()


def _signal_handler(signum: int, frame: object) -> None:
    signame = signal.Signals(signum).name
    glogger.info(f"Received {signame} — shutting down...")
    shutdown_event.set()


def main() -> None:
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    startup_rows = [
        ["version", __version__],
        ["github", "https://github.com/vroomfondel/flickr-immich-k8s-sync-operator"],
        ["pypi", "https://pypi.org/project/flickr-immich-k8s-sync-operator"],
        ["Docker Hub", "https://hub.docker.com/r/xomoxcc/flickr-immich-k8s-sync-operator"],
    ]
    table_str = tabulate(startup_rows, tablefmt="mixed_grid")
    lines = table_str.split("\n")
    table_width = len(lines[0])
    title = "flickr-immich-k8s-sync-operator starting up"
    title_border = "┍" + "━" * (table_width - 2) + "┑"
    title_row = "│ " + title.center(table_width - 4) + " │"
    separator = lines[0].replace("┍", "┝").replace("┑", "┥").replace("┯", "┿")

    glogger.opt(raw=True).info(
        "\n{}\n", title_border + "\n" + title_row + "\n" + separator + "\n" + "\n".join(lines[1:])
    )

    try:
        cfg = OperatorConfig.from_env()
        config_table = [[f.name, getattr(cfg, f.name)] for f in fields(cfg)]
        cfg_table_str = tabulate(config_table, tablefmt="mixed_grid")
        cfg_lines = cfg_table_str.split("\n")
        cfg_width = len(cfg_lines[0])
        cfg_title = "configuration"
        cfg_title_border = "┍" + "━" * (cfg_width - 2) + "┑"
        cfg_title_row = "│ " + cfg_title.center(cfg_width - 4) + " │"
        cfg_separator = cfg_lines[0].replace("┍", "┝").replace("┑", "┥").replace("┯", "┿")

        glogger.opt(raw=True).info(
            "\n{}\n",
            cfg_title_border + "\n" + cfg_title_row + "\n" + cfg_separator + "\n" + "\n".join(cfg_lines[1:]),
        )
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
