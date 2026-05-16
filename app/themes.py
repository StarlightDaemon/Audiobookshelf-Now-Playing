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
}

DEFAULT_THEME = "dark"
