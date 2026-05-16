#!/usr/bin/env bash

# Copyright (c) 2026 StarlightDaemon
# License: MIT | https://github.com/StarlightDaemon/audiobookshelf-now-playing/raw/main/LICENSE
# Source: https://www.audiobookshelf.org/ | Github: https://github.com/StarlightDaemon/audiobookshelf-now-playing

# Styling and message helpers from community-scripts (read-only, no build.func —
# their install URL is hardcoded to their repo and cannot be redirected).
source <(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/core.func)

APP="Audiobookshelf Now Playing"
NSAPP="audiobookshelf-now-playing"
var_tags="${var_tags:-audiobookshelf;media}"
var_cpu="${var_cpu:-1}"
var_ram="${var_ram:-512}"
var_disk="${var_disk:-4}"
var_os="${var_os:-debian}"
var_version="${var_version:-12}"
var_unprivileged="${var_unprivileged:-1}"

INSTALL_URL="https://raw.githubusercontent.com/StarlightDaemon/audiobookshelf-now-playing/main/deploy/install/audiobookshelf-now-playing-install.sh"

header_info "$APP"
color
catch_errors

# ── Update helper (run inside existing container) ─────────────────────────────
function update_script() {
  header_info
  if [[ -z "${CTID:-}" ]]; then
    msg_error "CTID is not set. Run: CTID=<vmid> bash $(basename "$0") update"
    exit 1
  fi
  msg_info "Updating ${APP}"
  pct exec "$CTID" -- bash -c "
    git -C /opt/audiobookshelf-now-playing pull --ff-only
    /opt/audiobookshelf-now-playing/venv/bin/pip install -q \
      -r /opt/audiobookshelf-now-playing/requirements.txt
    systemctl restart audiobookshelf-now-playing
  "
  msg_ok "Updated ${APP}"
  exit
}
[[ "${1:-}" == "update" ]] && update_script

# ── Preflight ─────────────────────────────────────────────────────────────────
if ! command -v pct &>/dev/null; then
  msg_error "This script must be run on a Proxmox VE host."
  exit 1
fi

# ── Container ID ──────────────────────────────────────────────────────────────
CTID=$(pvesh get /cluster/nextid 2>/dev/null)
msg_info "Using container ID ${CTID}"

# ── Debian template ───────────────────────────────────────────────────────────
TEMPLATE=$(pveam list local 2>/dev/null \
  | awk -v ver="debian-${var_version}" '$0 ~ ver {print $1}' \
  | sort -V | tail -n1)

if [[ -z "$TEMPLATE" ]]; then
  msg_info "Downloading Debian ${var_version} template"
  $STD pveam update
  TEMPLATE_NAME=$(pveam available --section system 2>/dev/null \
    | awk -v ver="debian-${var_version}-standard" '$0 ~ ver {print $1}' \
    | sort -V | tail -n1)
  [[ -z "$TEMPLATE_NAME" ]] && { msg_error "No Debian ${var_version} template available."; exit 1; }
  $STD pveam download local "$TEMPLATE_NAME"
  TEMPLATE="local:vztmpl/${TEMPLATE_NAME}"
  msg_ok "Downloaded Debian ${var_version} template"
fi

# ── Create container ──────────────────────────────────────────────────────────
msg_info "Creating LXC container ${CTID} (${var_cpu} core · ${var_ram}MB · ${var_disk}GB)"
$STD pct create "$CTID" "$TEMPLATE" \
  --hostname "$NSAPP" \
  --cores   "$var_cpu" \
  --memory  "$var_ram" \
  --rootfs  "local-lvm:${var_disk}" \
  --net0    name=eth0,bridge=vmbr0,ip=dhcp \
  --tags    "$var_tags" \
  --unprivileged "$var_unprivileged" \
  --features keyctl=1,nesting=1 \
  --onboot  1 \
  --start   0
msg_ok "Created LXC container ${CTID}"

# ── Start ─────────────────────────────────────────────────────────────────────
msg_info "Starting LXC container ${CTID}"
$STD pct start "$CTID"
# Wait for network to come up inside the container
for i in $(seq 1 10); do
  sleep 2
  pct exec "$CTID" -- bash -c "ip route get 1.1.1.1" &>/dev/null && break
done
msg_ok "Started LXC container ${CTID}"

# ── Install ───────────────────────────────────────────────────────────────────
msg_info "Running install script inside container"
pct exec "$CTID" -- bash -c "$(curl -fsSL "$INSTALL_URL")"
msg_ok "Install script complete"

# ── Final output ──────────────────────────────────────────────────────────────
IP=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}')

msg_ok "Completed successfully!\n"
echo -e "${CREATING}${GN}${APP} setup has been successfully initialized!${CL}"
echo -e "${INFO}${YW} Access it using the following URL:${CL}"
echo -e "${TAB}${GATEWAY}${BGN}http://${IP}:8000${CL}"
echo -e "${INFO}${YW} Set ABS credentials before the service will return data:${CL}"
echo -e "${TAB}${YW}pct exec ${CTID} -- nano /etc/audiobookshelf-now-playing.env${CL}"
echo -e "${INFO}${YW} Then restart:${CL}"
echo -e "${TAB}${YW}pct exec ${CTID} -- systemctl restart audiobookshelf-now-playing${CL}"
