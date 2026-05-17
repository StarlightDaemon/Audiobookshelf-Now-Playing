"""
Loads resolved Fujin design tokens from tokens-resolved.json and maps them
to the CSS custom property names used by settings_ui.py.

Load order (first success wins):
  1. FUJIN_TOKENS env var — explicit override path
  2. app/fujin-tokens-resolved.json — local copy committed to this repo (works in LXC)
  3. ../../Fujin/dist/tokens-resolved.json — sibling Fujin checkout (dev machine)
  4. Hardcoded fallback — values from Fujin dark Slate + violet[6] as of v0.1.0

To update tokens: run `npm run export-tokens` in the Fujin repo, copy
dist/tokens-resolved.json here as app/fujin-tokens-resolved.json, commit.
"""

import json
import os
from pathlib import Path

_HERE = Path(__file__).parent

_SEARCH_PATHS = [
    os.environ.get('FUJIN_TOKENS', ''),
    str(_HERE / 'fujin-tokens-resolved.json'),
    str(_HERE.parent.parent / 'Fujin' / 'dist' / 'tokens-resolved.json'),
]

# Maps local CSS var name → Fujin semantic token name
_VAR_MAP = {
    '--bg':       '--fujin-bg-base',
    '--surface':  '--fujin-bg-surface',
    '--surface2': '--fujin-bg-elevated',
    '--border':   '--fujin-border-default',
    '--accent':   '--fujin-interactive-default',
    '--text':     '--fujin-text-primary',
    '--text-dim': '--fujin-text-muted',
    '--success':  '--fujin-status-success',
}

# Fallback — Fujin dark Slate palette + violet[6], v0.1.0
_FALLBACK: dict[str, str] = {
    '--bg':          '#1f1f1f',
    '--surface':     '#242424',
    '--surface2':    '#2e2e2e',
    '--border':      '#3b3b3b',
    '--accent':      '#7950f2',
    '--accent-dim':  'rgba(121,80,242,0.15)',
    '--text':        '#c9c9c9',
    '--text-dim':    '#696969',
    '--success':     '#40c057',
    '--font':        '"Verdana", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    '--font-mono':   '"JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, Consolas, monospace',
}


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


def load_dark_tokens() -> dict[str, str]:
    """Return a CSS vars dict for the settings_ui.py :root block."""
    for path in _SEARCH_PATHS:
        if not path:
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            dark = data['dark']
            token_data = data.get('tokens', {})
            result: dict[str, str] = {}
            for local, fujin in _VAR_MAP.items():
                if fujin in dark:
                    result[local] = dark[fujin]
            result['--font']      = token_data.get('fontFamily',     _FALLBACK['--font'])
            result['--font-mono'] = token_data.get('fontFamilyMono', _FALLBACK['--font-mono'])
            accent = result.get('--accent', _FALLBACK['--accent'])
            result['--accent-dim'] = _hex_to_rgba(accent, 0.15)
            return result
        except Exception:
            continue
    return dict(_FALLBACK)
