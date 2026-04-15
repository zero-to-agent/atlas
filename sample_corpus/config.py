"""Configuration loading from environment variables and YAML files."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yml"

# Global settings dict, populated at import time
settings: Dict[str, Any] = {}


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file, then overlay environment variables.

    Environment variables prefixed with ``APP_`` take precedence over
    values found in the YAML file.  For example, ``APP_DATABASE_URL``
    overrides the ``DATABASE_URL`` key in the config file.

    Args:
        path: Path to the YAML configuration file.  Falls back to
              ``config.yml`` next to this module if not provided.

    Returns:
        Merged configuration dictionary.
    """
    config_path = Path(path) if path else _DEFAULT_CONFIG_PATH
    file_config: Dict[str, Any] = {}

    if config_path.exists():
        with open(config_path, "r") as fh:
            file_config = yaml.safe_load(fh) or {}

    # Overlay environment variables (APP_ prefix)
    for key, value in os.environ.items():
        if key.startswith("APP_"):
            config_key = key[4:]  # strip APP_ prefix
            file_config[config_key] = value

    return file_config


def get(key: str, default: Any = None) -> Any:
    """Retrieve a single configuration value.

    Args:
        key: Configuration key to look up.
        default: Value returned when the key is absent.

    Returns:
        The configuration value, or *default*.
    """
    return settings.get(key, default)


# Auto-load on import so other modules can use ``config.settings`` directly
settings.update(load_config())
