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
    "landscape-classic", "landscape-compact", "landscape-editorial", "landscape-minimal",
    "portrait-cover", "portrait-frosted",
    "portrait-typeset", "portrait-bookmark", "portrait-dogear",
    "portrait-spine", "portrait-spine-wide",
}
VALID_THEMES = {"light", "github-dark", "parchment", "kraft"}
VALID_CORNERS = {"rounded", "square"}


@dataclass
class AppConfig:
    layout: str = "landscape-classic"
    theme: str = "github-dark"
    label: str = "Currently Reading"
    corners: str = "rounded"


def load_config() -> AppConfig:
    try:
        with open(_CONFIG_PATH) as f:
            data = json.load(f)
        layout = data.get("layout", "landscape")
        theme = data.get("theme", "github-dark")
        label = data.get("label", "Currently Reading")
        corners = data.get("corners", "rounded")
        if layout not in VALID_LAYOUTS:
            layout = "landscape-classic"
        if theme not in VALID_THEMES:
            theme = "github-dark"
        if not isinstance(label, str) or not label.strip():
            label = "Currently Reading"
        if corners not in VALID_CORNERS:
            corners = "rounded"
        return AppConfig(layout=layout, theme=theme, label=label, corners=corners)
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
