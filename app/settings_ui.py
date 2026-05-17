from .config import AppConfig
from .fujin_tokens import load_dark_tokens

_LAYOUTS = [
    ("landscape-classic",   "Classic",    "600 × 160"),
    ("landscape-compact",   "Compact",    "600 × 80"),
    ("landscape-editorial", "Editorial",  "600 × 200"),
    ("portrait-cover",      "Cover",      "240 × 360"),
    ("portrait-frosted",    "Frosted",    "240 × 360"),
    ("portrait-typeset",    "Typeset",    "240 × 360"),
    ("portrait-bookmark",   "Bookmark",   "165 × 460"),
    ("portrait-dogear",     "Dog-ear",    "220 × 300"),
]

_THEMES = [
    ("light",       "Light"),
    ("github-dark", "GitHub Dark"),
    ("parchment",   "Parchment"),
    ("kraft",       "Kraft"),
]

_CORNERS = [
    ("rounded", "Rounded"),
    ("square",  "Square"),
]

_DEMO_URLS = {
    "landscape-classic":   "/cardlandscapedemo",
    "landscape-compact":   "/cardlandscapecdemo",
    "landscape-editorial": "/cardlandscapeddemo",
    "portrait-cover":      "/cardportraitdemo",
    "portrait-frosted":    "/cardportraitcdemo",
    "portrait-typeset":    "/cardportraitedemo",
    "portrait-bookmark":   "/cardportraitfdemo",
    "portrait-dogear":     "/cardportraitgdemo",
}


def build_settings_page(config: AppConfig, base_url: str = "") -> str:
    t = load_dark_tokens()
    layout_options = ""
    for key, name, dims in _LAYOUTS:
        sel = " selected" if key == config.layout else ""
        layout_options += f'<option value="{key}"{sel}>{name} — {dims}</option>\n'

    theme_options = ""
    for key, label in _THEMES:
        sel = " selected" if key == config.theme else ""
        theme_options += f'<option value="{key}"{sel}>{label}</option>\n'

    corners_options = ""
    for key, label in _CORNERS:
        sel = " selected" if key == config.corners else ""
        corners_options += f'<option value="{key}"{sel}>{label}</option>\n'

    demo_urls_js = "{\n" + ",\n".join(
        f'    "{k}": "{v}"' for k, v in _DEMO_URLS.items()
    ) + "\n  }"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ABS Now Playing — Settings</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:        {t['--bg']};
      --surface:   {t['--surface']};
      --surface2:  {t['--surface2']};
      --border:    {t['--border']};
      --accent:    {t['--accent']};
      --accent-dim: {t['--accent-dim']};
      --text:      {t['--text']};
      --text-dim:  {t['--text-dim']};
      --success:   {t['--success']};
      --font:      {t['--font']};
      --font-mono: {t['--font-mono']};
    }}

    body {{
      font-family: var(--font);
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    header {{
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      display: flex;
      align-items: center;
      gap: 12px;
      background: var(--surface);
    }}

    header h1 {{
      font-size: 16px;
      font-weight: 600;
      color: var(--text);
    }}

    header .sub {{
      font-size: 12px;
      color: var(--text-dim);
    }}

    .dot {{
      width: 8px; height: 8px;
      background: var(--accent);
      flex-shrink: 0;
    }}

    .main {{
      display: flex;
      flex: 1;
      gap: 0;
      overflow: hidden;
    }}

    .sidebar {{
      width: 320px;
      flex-shrink: 0;
      border-right: 1px solid var(--border);
      overflow-y: auto;
      padding: 20px 16px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    .preview-pane {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      padding: 32px 24px;
      gap: 24px;
      overflow-y: auto;
    }}

    .section-label {{
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-dim);
      margin-bottom: 8px;
    }}

    .label-select, .label-input {{
      width: 100%;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 0;
      padding: 8px 10px;
      font-family: var(--font);
      font-size: 13px;
      color: var(--text);
      outline: none;
      transition: border-color 0.15s;
      appearance: none;
      -webkit-appearance: none;
    }}

    .label-select {{
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238b949e' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      padding-right: 28px;
      cursor: pointer;
    }}

    .label-select:focus, .label-input:focus {{
      border-color: var(--accent);
    }}

    .label-input::placeholder {{
      color: var(--text-dim);
    }}

    .label-custom {{
      margin-top: 6px;
      display: none;
    }}

    .label-custom.visible {{
      display: block;
    }}

    .preview-card {{
      max-width: 100%;
      overflow: hidden;
      box-shadow: 0 4px 8px rgba(0,0,0,0.6);
      transition: opacity 0.15s;
    }}

    .preview-card img {{
      display: block;
      max-width: 100%;
      height: auto;
    }}

    .preview-loading {{
      opacity: 0.5;
    }}

    .embed-box {{
      width: 100%;
      max-width: 600px;
    }}

    .embed-box .label {{
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-dim);
      margin-bottom: 8px;
    }}

    .embed-row {{
      display: flex;
      gap: 8px;
    }}

    .embed-url {{
      flex: 1;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 0;
      padding: 8px 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-dim);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      user-select: all;
    }}

    .btn {{
      padding: 8px 14px;
      border-radius: 0;
      border: 1px solid var(--border);
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
      font-family: var(--font);
      transition: background 0.15s, border-color 0.15s, color 0.15s;
      white-space: nowrap;
    }}

    .btn-copy {{
      background: var(--surface2);
      color: var(--text);
    }}

    .btn-copy:hover {{
      background: var(--border);
    }}

    .btn-save {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}

    .btn-save:hover {{
      filter: brightness(1.1);
    }}

    .btn-save:disabled {{
      opacity: 0.5;
      cursor: not-allowed;
    }}

    .toast {{
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(80px);
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 0;
      padding: 10px 20px;
      font-size: 13px;
      color: var(--text);
      transition: transform 0.25s ease, opacity 0.25s ease;
      opacity: 0;
      pointer-events: none;
      z-index: 999;
    }}

    .toast.show {{
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }}

    .toast.success {{ border-color: var(--success); color: var(--success); }}
    .toast.error   {{ border-color: #f85149; color: #f85149; }}

    .actions {{
      width: 100%;
      max-width: 600px;
      display: flex;
      justify-content: flex-end;
    }}

    @media (max-width: 700px) {{
      .main {{ flex-direction: column; }}
      .sidebar {{ width: 100%; border-right: none; border-bottom: 1px solid var(--border); }}
      .preview-pane {{ padding: 20px 16px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="dot"></div>
    <div>
      <h1>Audiobookshelf Now Playing</h1>
      <div class="sub">Card settings &amp; preview</div>
    </div>
  </header>

  <div class="main">
    <div class="sidebar">
      <div>
        <div class="section-label">Layout</div>
        <select class="label-select" id="layout-select" onchange="selectLayout(this.value)">
          {layout_options}
        </select>
      </div>

      <div>
        <div class="section-label">Theme</div>
        <select class="label-select" id="theme-select" onchange="selectTheme(this.value)">
          {theme_options}
        </select>
      </div>

      <div>
        <div class="section-label">Corners</div>
        <select class="label-select" id="corners-select" onchange="selectCorners(this.value)">
          {corners_options}
        </select>
      </div>

      <div>
        <div class="section-label">Card label</div>
        <select class="label-select" id="label-select" onchange="onLabelSelect(this.value)">
          <option value="Currently Reading">Currently Reading</option>
          <option value="Now Reading">Now Reading</option>
          <option value="Reading">Reading</option>
          <option value="Listening To">Listening To</option>
          <option value="Now Listening">Now Listening</option>
          <option value="Currently Listening">Currently Listening</option>
          <option value="__custom__">Custom…</option>
        </select>
        <div class="label-custom" id="label-custom-wrap">
          <input class="label-input" id="label-input" type="text"
                 placeholder="Enter custom label"
                 oninput="onLabelInput(this.value)">
        </div>
      </div>
    </div>

    <div class="preview-pane">
      <div class="preview-card" id="preview-wrap">
        <img id="preview-img" src="" alt="Card preview">
      </div>

      <div class="embed-box">
        <div class="label">Your card URL — paste this anywhere</div>
        <div class="embed-row">
          <div class="embed-url" id="card-url"></div>
          <button class="btn btn-copy" onclick="copyCardUrl()">Copy</button>
        </div>
      </div>

      <div class="embed-box">
        <div class="label">GitHub README — paste directly into your markdown</div>
        <div class="embed-row">
          <div class="embed-url" id="md-snippet"></div>
          <button class="btn btn-copy" onclick="copyMarkdown()">Copy</button>
        </div>
      </div>

      <div class="actions">
        <button class="btn btn-save" id="btn-save" onclick="saveConfig()">Save &amp; apply</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>

  <script>
    const DEMO_URLS = {demo_urls_js};

    const LABEL_PRESETS = [
      "Currently Reading", "Now Reading", "Reading",
      "Listening To", "Now Listening", "Currently Listening",
    ];

    let currentLayout  = "{config.layout}";
    let currentTheme   = "{config.theme}";
    let currentLabel   = "{config.label}";
    let currentCorners = "{config.corners}";
    let labelDebounce  = null;

    function initLabel() {{
      const sel = document.getElementById("label-select");
      const inp = document.getElementById("label-input");
      const wrap = document.getElementById("label-custom-wrap");
      if (LABEL_PRESETS.includes(currentLabel)) {{
        sel.value = currentLabel;
      }} else {{
        sel.value = "__custom__";
        inp.value = currentLabel;
        wrap.classList.add("visible");
      }}
    }}

    function onLabelSelect(val) {{
      const wrap = document.getElementById("label-custom-wrap");
      if (val === "__custom__") {{
        wrap.classList.add("visible");
        const inp = document.getElementById("label-input");
        currentLabel = inp.value;
        inp.focus();
      }} else {{
        wrap.classList.remove("visible");
        currentLabel = val;
        updatePreview();
      }}
    }}

    function updatePreview() {{
      const img = document.getElementById("preview-img");
      const wrap = document.getElementById("preview-wrap");
      wrap.classList.add("preview-loading");

      let demoUrl = DEMO_URLS[currentLayout] + "?theme=" + currentTheme;
      if (currentLabel) demoUrl += "&label=" + encodeURIComponent(currentLabel);
      demoUrl += "&corners=" + currentCorners;
      demoUrl += "&_t=" + Date.now();
      img.onload = () => wrap.classList.remove("preview-loading");
      img.onerror = () => wrap.classList.remove("preview-loading");
      img.src = demoUrl;

      const cardUrl = window.location.origin + "/card";
      document.getElementById("card-url").textContent = cardUrl;
      document.getElementById("md-snippet").textContent = "![Now Playing](" + cardUrl + ")";
    }}

    function onLabelInput(val) {{
      currentLabel = val;
      clearTimeout(labelDebounce);
      labelDebounce = setTimeout(updatePreview, 400);
    }}

    function selectLayout(key) {{
      currentLayout = key;
      updatePreview();
    }}

    function selectTheme(t) {{
      currentTheme = t;
      updatePreview();
    }}

    function selectCorners(c) {{
      currentCorners = c;
      updatePreview();
    }}

    async function saveConfig() {{
      const btn = document.getElementById("btn-save");
      btn.disabled = true;
      try {{
        const resp = await fetch("/api/config", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ layout: currentLayout, theme: currentTheme, label: currentLabel, corners: currentCorners }}),
        }});
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        showToast("Saved as default", "success");
      }} catch (e) {{
        showToast("Failed to save: " + e.message, "error");
      }} finally {{
        btn.disabled = false;
      }}
    }}

    function copyCardUrl() {{
      navigator.clipboard.writeText(window.location.origin + "/card")
        .then(() => showToast("Card URL copied", "success"));
    }}

    function copyMarkdown() {{
      const md = "![Now Playing](" + window.location.origin + "/card)";
      navigator.clipboard.writeText(md)
        .then(() => showToast("Markdown copied", "success"));
    }}

    function showToast(msg, type) {{
      const el = document.getElementById("toast");
      el.textContent = msg;
      el.className = "toast " + (type || "");
      // force reflow
      void el.offsetWidth;
      el.classList.add("show");
      setTimeout(() => el.classList.remove("show"), 2500);
    }}

    // Initial render
    initLabel();
    updatePreview();
  </script>
</body>
</html>"""
