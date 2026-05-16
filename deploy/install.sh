#!/usr/bin/env bash
# install.sh — LXC setup script for Audiobookshelf Now Playing
# Run as root inside the LXC container.
set -euo pipefail

APP_DIR=/opt/audiobookshelf-now-playing
ENV_FILE=/etc/audiobookshelf-now-playing.env
SERVICE=audiobookshelf-now-playing

# ── Dependencies ─────────────────────────────────────────────────────────────
apt-get update -q
apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git ca-certificates

# ── Service user ──────────────────────────────────────────────────────────────
if ! id abs-card &>/dev/null; then
    useradd --system --shell /usr/sbin/nologin --home-dir "$APP_DIR" abs-card
fi

# ── Application code ─────────────────────────────────────────────────────────
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    # Replace with your actual repo URL if hosting publicly
    git clone https://github.com/StarlightDaemon/audiobookshelf-now-playing "$APP_DIR"
fi

chown -R abs-card:abs-card "$APP_DIR"

# ── Python virtualenv ─────────────────────────────────────────────────────────
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# ── Environment file ──────────────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    cp "$APP_DIR/.env.example" "$ENV_FILE"
    chmod 640 "$ENV_FILE"
    chown root:abs-card "$ENV_FILE"
    echo ""
    echo ">>> Created $ENV_FILE from template."
    echo ">>> Edit it now to set ABS_HOST and ABS_TOKEN, then re-run or start the service."
fi

# ── systemd unit ──────────────────────────────────────────────────────────────
cp "$APP_DIR/deploy/$SERVICE.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"

echo ""
echo "Done. Service status:"
systemctl status "$SERVICE" --no-pager
