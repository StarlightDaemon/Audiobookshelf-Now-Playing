import json
import logging
import os
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.environ.get(
    "CONFIG_PATH",
    "/etc/audiobookshelf-now-playing-config.json",
)

VALID_LAYOUTS = {
    "landscape", "portrait", "portrait-b",
    "portrait-c", "portrait-d", "portrait-e",
}
VALID_THEMES = {"dark", "light", "github-dark", "amoled"}


@dataclass
class AppConfig:
    layout: str = "landscape"
    theme: str = "dark"
    label: str = "Currently Reading"


def load_config() -> AppConfig:
    try:
        with open(_CONFIG_PATH) as f:
            data = json.load(f)
        layout = data.get("layout", "landscape")
        theme = data.get("theme", "dark")
        label = data.get("label", "Currently Reading")
        if layout not in VALID_LAYOUTS:
            layout = "landscape"
        if theme not in VALID_THEMES:
            theme = "dark"
        if not isinstance(label, str) or not label.strip():
            label = "Currently Reading"
        return AppConfig(layout=layout, theme=theme, label=label)
    except FileNotFoundError:
        return AppConfig()
    except Exception:
        logger.exception("Failed to load config from %s", _CONFIG_PATH)
        return AppConfig()


def save_config(config: AppConfig) -> None:
    try:
        with open(_CONFIG_PATH, "w") as f:
            json.dump(asdict(config), f, indent=2)
    except Exception:
        logger.exception("Failed to save config to %s", _CONFIG_PATH)
        raise
