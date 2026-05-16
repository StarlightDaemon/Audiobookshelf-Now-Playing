#!/usr/bin/env bash

# Copyright (c) 2026 StarlightDaemon
# License: MIT | https://github.com/StarlightDaemon/audiobookshelf-now-playing/raw/main/LICENSE
# Source: https://www.audiobookshelf.org/ | Github: https://github.com/StarlightDaemon/audiobookshelf-now-playing

# When run via community-scripts' build.func the host injects FUNCTIONS_FILE_PATH.
# When run standalone (via our ct/ script), source core.func from CDN instead.
if [ -n "${FUNCTIONS_FILE_PATH:-}" ]; then
  source /dev/stdin <<<"$FUNCTIONS_FILE_PATH"
else
  source <(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/core.func)
  STD="${STD:-}"

  # Stubs for functions normally injected by build.func
  verb_ip6()             { :; }
  setting_up_container() { :; }
  network_check()        { :; }
  update_os()            { apt-get -y update >/dev/null; apt-get -y upgrade >/dev/null; }
  motd_ssh()             { :; }
  customize()            { :; }
  cleanup_lxc() {
    apt-get -y autoremove >/dev/null
    apt-get clean >/dev/null
    rm -rf /var/lib/apt/lists/*
  }
fi

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
$STD apt-get install -y python3 python3-pip python3-venv git ca-certificates
msg_ok "Installed Dependencies"

msg_info "Creating Service User"
useradd --system --shell /usr/sbin/nologin --home-dir "$APP_DIR" abs-card
msg_ok "Created Service User"

msg_info "Installing ${APP:-Audiobookshelf Now Playing}"
$STD git clone https://github.com/StarlightDaemon/audiobookshelf-now-playing "$APP_DIR"
python3 -m venv "$APP_DIR/venv"
$STD "$APP_DIR/venv/bin/pip" install --upgrade pip
$STD "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
chown -R abs-card:abs-card "$APP_DIR"
msg_ok "Installed ${APP:-Audiobookshelf Now Playing}"

msg_info "Setting Up Environment"
cp "$APP_DIR/.env.example" "$ENV_FILE"
chmod 640 "$ENV_FILE"
chown root:abs-card "$ENV_FILE"
msg_ok "Created ${ENV_FILE} (set ABS_HOST and ABS_TOKEN before starting)"

msg_info "Configuring Service"
cp "$APP_DIR/deploy/audiobookshelf-now-playing.service" /etc/systemd/system/
systemctl daemon-reload
$STD systemctl enable audiobookshelf-now-playing
msg_ok "Configured Service"

motd_ssh
customize
cleanup_lxc
