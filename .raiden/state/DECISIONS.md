# Decisions

## D-001 — Fujin integration approach: CSS alignment only (2026-05-17)

**Decision:** The settings page (`app/settings_ui.py`) adopts Fujin's visual language via
CSS custom property alignment. It does not become a React app and does not import Fujin
components directly.

**Options considered:**
- A) CSS alignment — replace baked-in CSS vars with Fujin token values. No new deps, no
  build step. Fujin's look without its components.
- B) Full React integration — add Vite bundle, rebuild settings page as React SPA using
  actual Fujin components (FujinShell, selects, toasts, etc.).

**Rationale for A:** The settings page is a utility screen operators open once to get their
card URL. The product is the SVG card, not the UI. Option B would add npm, a build step, and
deploy script complexity to a service whose current strength is `pip install` and done.
Option B is the right call only if the settings page grows significantly in scope — revisit
if that happens.

**Binding rule this creates:** Any new UI element added to `settings_ui.py` follows the
existing CSS var pattern. No `package.json` or React is introduced without a new explicit
decision.

---

## D-002 — Card/settings boundary: Fujin does not touch SVG cards (2026-05-17)

**Decision:** Fujin theming applies to `app/settings_ui.py` only. `app/render.py` and
`app/themes.py` are out of scope for Fujin permanently.

**Rationale:** The SVG cards have their own self-contained theme system (`Theme` dataclass,
6 named themes). Their colors are not Fujin tokens and must not be — cards are embedded in
third-party surfaces (GitHub READMEs, home automation dashboards) where the user selects
among the card's own named themes. Fujin's Slate palette is for workstation UI chrome, not
for embeddable image output.

**Binding rule this creates:** If a task says "apply Fujin theming," it means
`settings_ui.py` only. No Fujin value (color, radius, font) may be written into
`render.py` or `themes.py`.
