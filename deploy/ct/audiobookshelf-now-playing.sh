#!/usr/bin/env bash

# Copyright (c) 2026 StarlightDaemon
# License: MIT | https://github.com/StarlightDaemon/audiobookshelf-now-playing/raw/main/LICENSE
# Source: https://www.audiobookshelf.org/ | Github: https://github.com/StarlightDaemon/audiobookshelf-now-playing

# ── Inline community-scripts style helpers ────────────────────────────────────
# Avoids sourcing core.func so the script is self-contained and testable
# without a network dependency on the Proxmox host.
YW=$(printf '\033[33m')
GN=$(printf '\033[32m')
RD=$(printf '\033[01;31m')
BL=$(printf '\033[36m')
CL=$(printf '\033[m')
CM="  ✔  "
CROSS="  ✖  "
INFO="  ℹ  "
TAB="  "
STD=""

msg_info()  { printf "  ${BL}%-50s${CL}" "${1}..."; }
msg_ok()    { printf " ${CM}${GN}%s${CL}\n" "${1}"; }
msg_error() { printf "\n ${CROSS}${RD}%s${CL}\n" "${1}" >&2; exit 1; }
msg_warn()  { printf "\n  ${INFO}${YW}%s${CL}\n" "${1}"; }

header_info() {
  printf "\n${BL}  %s${CL}\n%s\n" "${1}" "$(printf '─%.0s' {1..60})"
}

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

# ── Preflight ─────────────────────────────────────────────────────────────────
if ! command -v pct &>/dev/null; then
  msg_error "This script must be run on a Proxmox VE host."
fi

# ── Update helper (run inside existing container) ─────────────────────────────
function update_script() {
  header_info "$APP"
  if [[ -z "${CTID:-}" ]]; then
    msg_error "CTID is not set. Run: CTID=<vmid> bash $(basename "$0") update"
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

# ── Container ID ──────────────────────────────────────────────────────────────
CTID=$(pvesh get /cluster/nextid 2>/dev/null)
msg_info "Using container ID ${CTID}"
msg_ok "Container ID ${CTID}"

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
  [[ -z "$TEMPLATE_NAME" ]] && msg_error "No Debian ${var_version} template available."
  $STD pveam download local "$TEMPLATE_NAME"
  TEMPLATE="local:vztmpl/${TEMPLATE_NAME}"
  msg_ok "Downloaded Debian ${var_version} template"
fi

# ── Create container ──────────────────────────────────────────────────────────
msg_info "Creating LXC container ${CTID} (${var_cpu} core · ${var_ram}MB · ${var_disk}GB)"
$STD pct create "$CTID" "$TEMPLATE" \
  --hostname "$NSAPP" \
  --cores    "$var_cpu" \
  --memory   "$var_ram" \
  --rootfs   "local-lvm:${var_disk}" \
  --net0     name=eth0,bridge=vmbr0,ip=dhcp \
  --tags     "$var_tags" \
  --unprivileged "$var_unprivileged" \
  --features keyctl=1,nesting=1 \
  --onboot   1 \
  --start    0
msg_ok "Created LXC container ${CTID}"

# ── Start ─────────────────────────────────────────────────────────────────────
msg_info "Starting LXC container ${CTID}"
$STD pct start "$CTID"
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

printf "\n${GN}  ✔  ${APP} setup has been successfully initialized!${CL}\n"
printf "\n${YW}  ℹ  Access it using the following URL:${CL}\n"
printf "${TAB}${TAB}${BL}http://${IP}:8000${CL}\n"
printf "\n${YW}  ℹ  Set ABS credentials before the service will return data:${CL}\n"
printf "${TAB}${TAB}${YW}pct exec ${CTID} -- nano /etc/audiobookshelf-now-playing.env${CL}\n"
printf "\n${YW}  ℹ  Then restart:${CL}\n"
printf "${TAB}${TAB}${YW}pct exec ${CTID} -- systemctl restart audiobookshelf-now-playing${CL}\n\n"
