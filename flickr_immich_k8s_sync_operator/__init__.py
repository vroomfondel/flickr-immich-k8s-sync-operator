"""Package initialisation — version constant and loguru configuration helper."""

__version__ = "0.0.4"

import os
import sys
from typing import Any, Callable, Dict

from loguru import logger as glogger

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
