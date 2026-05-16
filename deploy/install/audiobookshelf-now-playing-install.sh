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
  STD=""

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
useradd --system --shell /usr/sbin/nologin --home-dir "$APP_DIR" abs-card
msg_ok "Created Service User"

msg_info "Cloning Repository"
$STD git clone https://github.com/StarlightDaemon/Audiobookshelf-Now-Playing "$APP_DIR"
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

motd_ssh
customize
cleanup_lxc
