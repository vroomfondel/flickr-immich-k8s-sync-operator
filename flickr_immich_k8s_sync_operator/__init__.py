"""Package initialisation — version constant, loguru configuration, and startup banner."""

from __future__ import annotations

__version__ = "0.0.6"

import os
import sys
from dataclasses import fields
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Sequence

from loguru import logger as glogger
from tabulate import tabulate

if TYPE_CHECKING:
    from flickr_immich_k8s_sync_operator.config import OperatorConfig

glogger.disable(__name__)


def _loguru_skiplog_filter(record: dict) -> bool:  # type: ignore[type-arg]
    """Filter log records that have the ``skiplog`` extra flag set.

    Args:
        record: A loguru record dictionary.

    Returns:
        ``False`` when the record should be suppressed, ``True`` otherwise.
    """
    return not record.get("extra", {}).get("skiplog", False)


def configure_logging(
    loguru_filter: Callable[[Dict[str, Any]], bool] = _loguru_skiplog_filter,
) -> None:
    """Configure a default loguru sink with a structured format and optional filter.

    Sets up a single stderr sink with timestamp, level, module, class name,
    function, and line number.  Defaults ``LOGURU_LEVEL`` to ``DEBUG`` if the
    environment variable is not already set.

    Args:
        loguru_filter: A callable that receives a loguru record dict and
            returns ``True`` to keep the record or ``False`` to suppress it.
            Defaults to :func:`_loguru_skiplog_filter`.
    """
    os.environ["LOGURU_LEVEL"] = os.getenv("LOGURU_LEVEL", "DEBUG")
    glogger.remove()
    logger_fmt: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>::<cyan>{extra[classname]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    glogger.add(sys.stderr, level=os.getenv("LOGURU_LEVEL"), format=logger_fmt, filter=loguru_filter)  # type: ignore[arg-type]
    glogger.configure(extra={"classname": "None", "skiplog": False})


def _titled_table(title: str, rows: Sequence[Sequence[object]]) -> str:
    """Render a ``tabulate`` table with a centred title row above it.

    Args:
        title: Text displayed in the title row.
        rows: Table body rows passed to ``tabulate``.

    Returns:
        The complete table string including the title header.
    """
    table_str = tabulate(rows, tablefmt="mixed_grid")
    lines = table_str.split("\n")
    width = len(lines[0])
    title_border = "┍" + "━" * (width - 2) + "┑"
    title_row = "│ " + title.center(width - 4) + " │"
    separator = lines[0].replace("┍", "┝").replace("┑", "┥").replace("┯", "┿")
    return title_border + "\n" + title_row + "\n" + separator + "\n" + "\n".join(lines[1:])


def print_startup_banner(cfg: OperatorConfig) -> None:
    """Log the startup banner and the active operator configuration.

    Prints two titled tables via loguru: one with version and project links,
    and one with all fields of the configuration dataclass.

    Args:
        cfg: The active operator configuration.
    """
    startup_rows: List[List[object]] = [
        ["version", __version__],
        ["github", "https://github.com/vroomfondel/flickr-immich-k8s-sync-operator"],
        ["pypi", "https://pypi.org/project/flickr-immich-k8s-sync-operator"],
        ["Docker Hub", "https://hub.docker.com/r/xomoxcc/flickr-immich-k8s-sync-operator"],
    ]
    glogger.opt(raw=True).info("\n{}\n", _titled_table("flickr-immich-k8s-sync-operator starting up", startup_rows))

    config_rows: List[List[object]] = [[f.name, getattr(cfg, f.name)] for f in fields(cfg)]
    glogger.opt(raw=True).info("\n{}\n", _titled_table("configuration", config_rows))
