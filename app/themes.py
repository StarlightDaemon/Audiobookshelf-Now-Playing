from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    background: str
    border: str
    accent: str
    text_primary: str
    text_secondary: str


THEMES: dict[str, Theme] = {
    "dark": Theme(
        background="#1e2229",
        border="#2e3340",
        accent="#4d8ef0",
        text_primary="#cdd5e0",
        text_secondary="#6b7585",
    ),
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
    "amoled": Theme(
        background="#000000",
        border="#1c1c1e",
        accent="#0a84ff",
        text_primary="#ffffff",
        text_secondary="#8e8e93",
    ),
}

DEFAULT_THEME = "dark"
