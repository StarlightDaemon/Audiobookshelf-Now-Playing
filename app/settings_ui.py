from .config import AppConfig

_LAYOUTS = [
    ("landscape",  "Landscape",  "600 × 160",  "Wide banner · cover + two metadata columns"),
    ("portrait",   "Portrait A", "240 × 360",  "Classic stacked · cover above text block"),
    ("portrait-b", "Portrait B", "240 × 360",  "Full-bleed cover · gradient overlay"),
    ("portrait-c", "Portrait C", "240 × 360",  "Blurred cover · frosted-glass panel"),
    ("portrait-d", "Portrait D", "240 × 360",  "Sidebar accent stripe · small thumbnail"),
    ("portrait-e", "Portrait E", "240 × 360",  "Editorial / typographic · large wrapped title"),
]

_DEMO_URLS = {
    "landscape":  "/cardlandscapedemo",
    "portrait":   "/cardportraitdemo",
    "portrait-b": "/cardportraitbdemo",
    "portrait-c": "/cardportraitcdemo",
    "portrait-d": "/cardportraitddemo",
    "portrait-e": "/cardportraitedemo",
}


def build_settings_page(config: AppConfig, base_url: str = "") -> str:
    layout_rows = ""
    for key, name, dims, desc in _LAYOUTS:
        sel = "selected" if key == config.layout else ""
        layout_rows += (
            f'<div class="layout-option {sel}" data-layout="{key}" onclick="selectLayout(\'{key}\')">'
            f'<div class="lo-header"><span class="lo-name">{name}</span>'
            f'<span class="lo-dims">{dims}</span></div>'
            f'<div class="lo-desc">{desc}</div>'
            f'</div>\n'
        )

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
      --bg: #0d1117;
      --surface: #161b22;
      --surface2: #21262d;
      --border: #30363d;
      --accent: #4d8ef0;
      --accent-dim: rgba(77,142,240,0.15);
      --text: #c9d1d9;
      --text-dim: #8b949e;
      --success: #3fb950;
      --radius: 8px;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      --font-mono: "Fira Code", "Courier New", monospace;
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
      width: 8px; height: 8px; border-radius: 50%;
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

    .layout-option {{
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 10px 12px;
      cursor: pointer;
      margin-bottom: 6px;
      transition: border-color 0.15s, background 0.15s;
    }}

    .layout-option:hover {{
      border-color: var(--accent);
      background: var(--accent-dim);
    }}

    .layout-option.selected {{
      border-color: var(--accent);
      background: var(--accent-dim);
    }}

    .lo-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 3px;
    }}

    .lo-name {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text);
    }}

    .lo-dims {{
      font-size: 11px;
      color: var(--text-dim);
      font-family: var(--font-mono);
    }}

    .lo-desc {{
      font-size: 11px;
      color: var(--text-dim);
    }}

    .label-input {{
      width: 100%;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 8px 10px;
      font-family: var(--font);
      font-size: 13px;
      color: var(--text);
      outline: none;
      transition: border-color 0.15s;
    }}

    .label-input:focus {{
      border-color: var(--accent);
    }}

    .label-input::placeholder {{
      color: var(--text-dim);
    }}

    .theme-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }}

    .theme-btn {{
      padding: 8px 0;
      text-align: center;
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
      transition: background 0.15s, color 0.15s, border-color 0.15s;
      color: var(--text-dim);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: transparent;
      outline: none;
    }}

    .theme-btn.active {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}

    .theme-btn:not(.active):hover {{
      background: var(--surface2);
      color: var(--text);
    }}

    .preview-card {{
      max-width: 100%;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,0.5);
      transition: opacity 0.2s;
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
      border-radius: var(--radius);
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
      border-radius: var(--radius);
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
      border-radius: var(--radius);
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
        {layout_rows}
      </div>

      <div>
        <div class="section-label">Card label</div>
        <input class="label-input" id="label-input" type="text"
               placeholder="Currently Reading"
               value="{config.label}"
               oninput="onLabelInput(this.value)">
      </div>

      <div>
        <div class="section-label">Theme</div>
        <div class="theme-grid">
          <button class="theme-btn {'active' if config.theme == 'dark' else ''}"
                  id="btn-dark" onclick="selectTheme('dark')">Dark</button>
          <button class="theme-btn {'active' if config.theme == 'light' else ''}"
                  id="btn-light" onclick="selectTheme('light')">Light</button>
          <button class="theme-btn {'active' if config.theme == 'github-dark' else ''}"
                  id="btn-github-dark" onclick="selectTheme('github-dark')">GitHub Dark</button>
          <button class="theme-btn {'active' if config.theme == 'amoled' else ''}"
                  id="btn-amoled" onclick="selectTheme('amoled')">AMOLED</button>
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

    let currentLayout = "{config.layout}";
    let currentTheme  = "{config.theme}";
    let currentLabel  = "{config.label}";
    let labelDebounce = null;

    function updatePreview() {{
      const img = document.getElementById("preview-img");
      const wrap = document.getElementById("preview-wrap");
      wrap.classList.add("preview-loading");

      let demoUrl = DEMO_URLS[currentLayout] + "?theme=" + currentTheme;
      if (currentLabel) demoUrl += "&label=" + encodeURIComponent(currentLabel);
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
      document.querySelectorAll(".layout-option").forEach(el => {{
        el.classList.toggle("selected", el.dataset.layout === key);
      }});
      updatePreview();
    }}

    const THEMES = ["dark", "light", "github-dark", "amoled"];

    function selectTheme(t) {{
      currentTheme = t;
      THEMES.forEach(k => {{
        document.getElementById("btn-" + k).classList.toggle("active", k === t);
      }});
      updatePreview();
    }}

    async function saveConfig() {{
      const btn = document.getElementById("btn-save");
      btn.disabled = true;
      try {{
        const resp = await fetch("/api/config", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ layout: currentLayout, theme: currentTheme, label: currentLabel }}),
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
    updatePreview();
  </script>
</body>
</html>"""
