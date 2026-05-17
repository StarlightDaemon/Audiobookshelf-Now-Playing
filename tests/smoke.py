"""
Smoke tests for all SVG renderer × theme combinations.

Runnable as:
    python tests/smoke.py          (standalone)
    python -m pytest tests/smoke.py -v   (via pytest)
"""

import sys
import os

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.render import (
    render_landscape_demo,
    render_portrait_demo,
    render_portrait_b_demo,
    render_portrait_c_demo,
    render_portrait_d_demo,
    render_portrait_e_demo,
)
from app.themes import THEMES

RENDERERS = [
    ("render_landscape_demo",   render_landscape_demo),
    ("render_portrait_demo",    render_portrait_demo),
    ("render_portrait_b_demo",  render_portrait_b_demo),
    ("render_portrait_c_demo",  render_portrait_c_demo),
    ("render_portrait_d_demo",  render_portrait_d_demo),
    ("render_portrait_e_demo",  render_portrait_e_demo),
]


def _check(renderer_name: str, theme_name: str, theme) -> tuple[bool, str]:
    """Return (passed, message) for a single renderer × theme combo."""
    try:
        result = renderer_name  # just to avoid shadowing
        svg = RENDERERS[[n for n, _ in RENDERERS].index(renderer_name)][1](theme)
    except Exception as exc:
        return False, f"EXCEPTION: {exc}"

    if not isinstance(svg, str):
        return False, f"result is {type(svg).__name__}, not str"
    if not svg.startswith("<svg"):
        return False, f"does not start with <svg (got {svg[:30]!r})"
    if not svg.endswith("</svg>"):
        return False, f"does not end with </svg> (got ...{svg[-30:]!r})"
    return True, "ok"


# ── pytest-compatible test functions ─────────────────────────────────────────

def _make_test(renderer_name, fn, theme_name, theme):
    def test_fn():
        try:
            svg = fn(theme)
        except Exception as exc:
            raise AssertionError(f"{renderer_name}({theme_name}): exception: {exc}") from exc
        assert isinstance(svg, str), (
            f"{renderer_name}({theme_name}): result is {type(svg).__name__}, not str"
        )
        assert svg.startswith("<svg"), (
            f"{renderer_name}({theme_name}): does not start with <svg"
        )
        assert svg.endswith("</svg>"), (
            f"{renderer_name}({theme_name}): does not end with </svg>"
        )
    test_fn.__name__ = f"test_{renderer_name}_{theme_name}"
    return test_fn


# Inject pytest-discoverable test functions into module namespace
for _rname, _rfn in RENDERERS:
    for _tname, _theme in THEMES.items():
        _t = _make_test(_rname, _rfn, _tname, _theme)
        globals()[_t.__name__] = _t


# ── Standalone runner ─────────────────────────────────────────────────────────

def _run_standalone() -> int:
    passed = 0
    failed = 0
    failures: list[str] = []

    for renderer_name, fn in RENDERERS:
        for theme_name, theme in THEMES.items():
            label = f"{renderer_name}({theme_name})"
            try:
                svg = fn(theme)
            except Exception as exc:
                msg = f"FAIL  {label}: exception: {exc}"
                print(msg)
                failures.append(msg)
                failed += 1
                continue

            ok = True
            reason = ""
            if not isinstance(svg, str):
                ok, reason = False, f"result is {type(svg).__name__}, not str"
            elif not svg.startswith("<svg"):
                ok, reason = False, f"does not start with <svg (got {svg[:30]!r})"
            elif not svg.endswith("</svg>"):
                ok, reason = False, f"does not end with </svg> (got ...{svg[-30:]!r})"

            if ok:
                print(f"PASS  {label}")
                passed += 1
            else:
                msg = f"FAIL  {label}: {reason}"
                print(msg)
                failures.append(msg)
                failed += 1

    total = passed + failed
    print(f"\n{passed}/{total} passed", end="")
    if failures:
        print(f", {failed} failed:")
        for f in failures:
            print(f"  {f}")
        return 1
    print()
    return 0


if __name__ == "__main__":
    sys.exit(_run_standalone())
