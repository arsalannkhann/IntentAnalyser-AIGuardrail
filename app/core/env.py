import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_ENV_LOADED_FLAG = "_INTENT_ANALYZER_ENV_LOADED"


def load_env_file(env_path: str = ".env") -> None:
    """
    Lightweight .env loader with no external dependency.
    Existing environment variables always take precedence.
    """
    if os.getenv(_ENV_LOADED_FLAG) == "1":
        return

    path = Path(env_path)
    if not path.exists():
        return

    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)
    except Exception as exc:
        logger.warning("Failed to load .env file '%s': %s", env_path, exc)
    finally:
        os.environ[_ENV_LOADED_FLAG] = "1"
