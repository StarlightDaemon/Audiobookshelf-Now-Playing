from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    background: str
    border: str
    accent: str
    text_primary: str
    text_secondary: str


THEMES: dict[str, Theme] = {
    "light": Theme(
        background="#f6f8fa",
        border="#d0d7de",
        accent="#0969da",
        text_primary="#1f2328",
        text_secondary="#57606a",
    ),
    "github-dark": Theme(
        background="#0d1117",
        border="#30363d",
        accent="#58a6ff",
        text_primary="#e6edf3",
        text_secondary="#8b949e",
    ),
    "parchment": Theme(
        background="#f5edd8",
        border="#cdb891",
        accent="#8b5e3c",
        text_primary="#2c1a0e",
        text_secondary="#7a5c3a",
    ),
    "kraft": Theme(
        background="#eddec4",
        border="#c4a07a",
        accent="#7a4a1e",
        text_primary="#231509",
        text_secondary="#8a6040",
    ),
}

DEFAULT_THEME = "github-dark"
