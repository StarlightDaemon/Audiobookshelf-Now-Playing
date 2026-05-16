#!/usr/bin/env bash

# Copyright (c) 2026 StarlightDaemon
# License: MIT | https://github.com/StarlightDaemon/audiobookshelf-now-playing/raw/main/LICENSE
# Source: https://www.audiobookshelf.org/ | Github: https://github.com/StarlightDaemon/audiobookshelf-now-playing

# ── Message helpers ───────────────────────────────────────────────────────────
# When run via community-scripts' build.func, FUNCTIONS_FILE_PATH is injected
# and provides msg_info, msg_ok, etc. from their toolchain.
# When run standalone (via our ct/ script), we inline equivalent helpers so
# there is no curl / CDN dependency inside the fresh container.
if [ -n "${FUNCTIONS_FILE_PATH:-}" ]; then
  source /dev/stdin <<<"$FUNCTIONS_FILE_PATH"
else
  YW=$(printf '\033[33m')
  GN=$(printf '\033[32m')
  RD=$(printf '\033[01;31m')
  BL=$(printf '\033[36m')
  CL=$(printf '\033[m')
  CM="  ✔  "
  CROSS="  ✖  "

  msg_info()  { printf "  ${BL}%-50s${CL}" "${1}..."; }
  msg_ok()    { printf " ${CM}${GN}%s${CL}\n" "${1}"; }
  msg_error() { printf "\n ${CROSS}${RD}%s${CL}\n" "${1}" >&2; exit 1; }

  verb_ip6()             { :; }
  catch_errors()         { set -euo pipefail; }
  setting_up_container() { :; }
  network_check()        { :; }
  update_os() {
    apt-get -y update  >/dev/null 2>&1
    apt-get -y upgrade >/dev/null 2>&1
  }
  motd_ssh()  { :; }
  customize() { :; }
  cleanup_lxc() {
    apt-get -y autoremove >/dev/null 2>&1
    apt-get clean        >/dev/null 2>&1
    rm -rf /var/lib/apt/lists/*
  }
fi

# ── Verbose / silent mode ─────────────────────────────────────────────────────
silent() { "$@" >/dev/null 2>&1; }
if [[ "${VERBOSE:-0}" == "1" ]]; then
  STD=""
else
  STD="silent"
fi

color()      { :; }   # no-op — colours already set above or via FUNCTIONS_FILE_PATH

color
verb_ip6
catch_errors
setting_up_container
network_check
update_os

APP_DIR=/opt/audiobookshelf-now-playing
ENV_FILE=/etc/audiobookshelf-now-playing.env
SERVICE=audiobookshelf-now-playing

msg_info "Installing Dependencies"
# python3-venv ships pip via ensurepip — no system python3-pip needed,
# which avoids pulling in 436 MB of build-essential / gcc toolchain.
$STD apt-get install -y python3 python3-venv git ca-certificates
msg_ok "Installed Dependencies"

msg_info "Creating Service User"
id abs-card &>/dev/null || useradd --system --shell /usr/sbin/nologin --home-dir "$APP_DIR" abs-card
msg_ok "Created Service User"

msg_info "Cloning Repository"
$STD git clone --depth 1 https://github.com/StarlightDaemon/Audiobookshelf-Now-Playing "$APP_DIR"
msg_ok "Cloned Repository"

msg_info "Installing Python Dependencies"
python3 -m venv "$APP_DIR/venv"
$STD "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
$STD "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
chown -R abs-card:abs-card "$APP_DIR"
msg_ok "Installed Python Dependencies"

msg_info "Setting Up Environment"
cp "$APP_DIR/.env.example" "$ENV_FILE"
chmod 640 "$ENV_FILE"
chown root:abs-card "$ENV_FILE"
msg_ok "Created ${ENV_FILE}"

msg_info "Configuring Systemd Service"
cp "$APP_DIR/deploy/audiobookshelf-now-playing.service" /etc/systemd/system/
systemctl daemon-reload
$STD systemctl enable audiobookshelf-now-playing
msg_ok "Configured Systemd Service"

msg_info "Installing Status MOTD"
# Symlink into the repo so 'update' (git pull) keeps MOTD current.
chmod +x "$APP_DIR/deploy/motd.sh"
ln -sf "$APP_DIR/deploy/motd.sh" /etc/update-motd.d/99-abs-status
rm -f /etc/motd
msg_ok "Installed Status MOTD"

msg_info "Configuring Console Auto-Login"
# Proxmox LXC containers use container-getty@1, not getty@tty1
GETTY_OVERRIDE="/etc/systemd/system/container-getty@1.service.d/override.conf"
mkdir -p "$(dirname "$GETTY_OVERRIDE")"
cat > "$GETTY_OVERRIDE" << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear --keep-baud tty%I 115200,38400,9600 $TERM
EOF
systemctl daemon-reload
systemctl restart container-getty@1 2>/dev/null || true
msg_ok "Configured Console Auto-Login"

msg_info "Installing Update Script"
# Thin wrapper — delegates to deploy/update.sh in the repo so the logic
# updates itself on every pull without needing a reinstall.
cat > /usr/local/bin/abs-now-playing-update << 'EOF'
#!/usr/bin/env bash
exec /opt/audiobookshelf-now-playing/deploy/update.sh "$@"
EOF
chmod +x /usr/local/bin/abs-now-playing-update
ln -sf /usr/local/bin/abs-now-playing-update /usr/bin/update
msg_ok "Installed Update Script"

motd_ssh
customize
cleanup_lxc
