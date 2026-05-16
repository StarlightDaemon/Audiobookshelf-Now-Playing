#!/usr/bin/env bash

# Copyright (c) 2026 StarlightDaemon
# License: MIT | https://github.com/StarlightDaemon/audiobookshelf-now-playing/raw/main/LICENSE
# Source: https://www.audiobookshelf.org/ | Github: https://github.com/StarlightDaemon/audiobookshelf-now-playing

# ── Colour helpers ────────────────────────────────────────────────────────────
YW=$(printf '\033[33m')
GN=$(printf '\033[32m')
RD=$(printf '\033[01;31m')
BL=$(printf '\033[36m')
CL=$(printf '\033[m')
CM="  ✔  "
CROSS="  ✖  "
INFO="  ℹ  "
TAB="  "

msg_info()  { printf "  ${BL}%-50s${CL}" "${1}..."; }
msg_ok()    { printf " ${CM}${GN}%s${CL}\n" "${1}"; }
msg_error() { printf "\n ${CROSS}${RD}%s${CL}\n" "${1}" >&2; exit 1; }
msg_warn()  { printf "\n  ${INFO}${YW}%s${CL}\n" "${1}"; }

# ── Verbose / silent mode ─────────────────────────────────────────────────────
# Pass --verbose as the first argument to see all subprocess output.
silent() { "$@" >/dev/null 2>&1; }
if [[ "${1:-}" == "--verbose" ]]; then
  VERBOSE=1
  STD=""
  shift
else
  VERBOSE=0
  STD="silent"
fi

# ── Banner ────────────────────────────────────────────────────────────────────
show_header() {
  clear
  printf "${BL}"
  printf '  ╔══════════════════════════════════════════════════════════╗\n'
  printf '  ║        Audiobookshelf Now Playing  —  LXC Installer      ║\n'
  printf '  ╚══════════════════════════════════════════════════════════╝\n'
  printf "${CL}\n"
}

APP="Audiobookshelf Now Playing"
NSAPP="audiobookshelf-now-playing"

# ── Defaults ──────────────────────────────────────────────────────────────────
var_tags="${var_tags:-audiobookshelf;media}"
var_cpu="${var_cpu:-1}"
var_ram="${var_ram:-256}"
var_disk="${var_disk:-2}"
var_os="${var_os:-debian}"
var_version="${var_version:-12}"
var_unprivileged="${var_unprivileged:-1}"
var_bridge="${var_bridge:-vmbr0}"

INSTALL_URL="https://raw.githubusercontent.com/StarlightDaemon/audiobookshelf-now-playing/main/deploy/install/audiobookshelf-now-playing-install.sh"

BACKTITLE="${APP} Installer"

show_header

# ── Update helper ─────────────────────────────────────────────────────────────
# Can be called two ways:
#   From Proxmox host : CTID=107 bash <(curl -fsSL .../ct/script.sh) update
#   From inside the container : bash <(curl -fsSL .../ct/script.sh) update
function update_script() {
  show_header
  APP_DIR=/opt/audiobookshelf-now-playing

  if command -v pct &>/dev/null; then
    # ── Running on Proxmox host ───────────────────────────────────────────────
    if [[ -z "${CTID:-}" ]]; then
      msg_error "CTID is not set. Run: CTID=<vmid> bash <(curl -fsSL ...) update"
    fi
    msg_info "Updating ${APP} in container ${CTID}"
    pct exec "$CTID" -- bash -c "
      set -euo pipefail
      APP_DIR=${APP_DIR}
      git -C \"\$APP_DIR\" fetch --depth 1 origin
      git -C \"\$APP_DIR\" reset --hard origin/HEAD
      \"\$APP_DIR/venv/bin/pip\" install -q -r \"\$APP_DIR/requirements.txt\"
      cat > /usr/local/bin/abs-now-playing-update << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR=/opt/audiobookshelf-now-playing
git -C \"\$APP_DIR\" fetch --depth 1 origin
git -C \"\$APP_DIR\" reset --hard origin/HEAD
\"\$APP_DIR/venv/bin/pip\" install -q -r \"\$APP_DIR/requirements.txt\"
systemctl restart audiobookshelf-now-playing
echo '  ✔  audiobookshelf-now-playing updated and restarted'
EOF
      chmod +x /usr/local/bin/abs-now-playing-update
      ln -sf /usr/local/bin/abs-now-playing-update /usr/local/bin/update
      systemctl restart audiobookshelf-now-playing
    "
    msg_ok "Updated ${APP}"
  else
    # ── Running inside the container ─────────────────────────────────────────
    if [[ ! -d "$APP_DIR" ]]; then
      msg_error "No installation found at ${APP_DIR}"
    fi
    msg_info "Updating ${APP}"
    git -C "$APP_DIR" fetch --depth 1 origin
    git -C "$APP_DIR" reset --hard origin/HEAD
    "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
    ln -sf /usr/local/bin/abs-now-playing-update /usr/local/bin/update
    systemctl restart audiobookshelf-now-playing
    msg_ok "Updated ${APP}"
  fi
  exit
}
[[ "${1:-}" == "update" ]] && update_script

# ── Preflight (install path only) ─────────────────────────────────────────────
if ! command -v pct &>/dev/null; then
  msg_error "This script must be run on a Proxmox VE host (or with 'update' argument inside a container)."
fi

if ! command -v whiptail &>/dev/null; then
  msg_error "whiptail is required. Install it with: apt-get install whiptail"
fi

# ── Resolve next available CT ID ──────────────────────────────────────────────
NEXT_ID=$(pvesh get /cluster/nextid 2>/dev/null || echo "100")

# ── Settings wizard ───────────────────────────────────────────────────────────
function advanced_settings() {
  local STEP=0 MAX_STEP=6

  # Step 0: CT ID
  while true; do
    STEP=1
    CT_ID=$(whiptail \
      --backtitle "$BACKTITLE" \
      --title "Container ID  [${STEP}/${MAX_STEP}]" \
      --ok-button "Next" --cancel-button "Cancel" \
      --inputbox "\nContainer ID for the new LXC:" 10 50 "$NEXT_ID" \
      3>&1 1>&2 2>&3) || return 1
    [[ "$CT_ID" =~ ^[0-9]+$ && "$CT_ID" -ge 100 ]] && break
    whiptail --backtitle "$BACKTITLE" --title "Invalid ID" \
      --msgbox "Container ID must be a number ≥ 100." 8 40
  done

  # Step 1: Hostname
  STEP=2
  CT_HOSTNAME=$(whiptail \
    --backtitle "$BACKTITLE" \
    --title "Hostname  [${STEP}/${MAX_STEP}]" \
    --ok-button "Next" --cancel-button "Back" \
    --inputbox "\nHostname for the container:" 10 50 "$NSAPP" \
    3>&1 1>&2 2>&3) || { STEP=1; advanced_settings; return; }
  CT_HOSTNAME="${CT_HOSTNAME:-$NSAPP}"

  # Step 2: CPU cores
  STEP=3
  CPU=$(whiptail \
    --backtitle "$BACKTITLE" \
    --title "CPU Cores  [${STEP}/${MAX_STEP}]" \
    --ok-button "Next" --cancel-button "Back" \
    --inputbox "\nNumber of CPU cores (1–8):" 10 50 "$var_cpu" \
    3>&1 1>&2 2>&3) || { advanced_settings; return; }
  CPU="${CPU:-$var_cpu}"

  # Step 3: RAM
  STEP=4
  RAM=$(whiptail \
    --backtitle "$BACKTITLE" \
    --title "RAM (MB)  [${STEP}/${MAX_STEP}]" \
    --ok-button "Next" --cancel-button "Back" \
    --inputbox "\nMemory in MB (minimum 256):" 10 50 "$var_ram" \
    3>&1 1>&2 2>&3) || { advanced_settings; return; }
  RAM="${RAM:-$var_ram}"

  # Step 4: Disk
  STEP=5
  DISK=$(whiptail \
    --backtitle "$BACKTITLE" \
    --title "Disk Size (GB)  [${STEP}/${MAX_STEP}]" \
    --ok-button "Next" --cancel-button "Back" \
    --inputbox "\nRoot disk size in GB (minimum 2):" 10 50 "$var_disk" \
    3>&1 1>&2 2>&3) || { advanced_settings; return; }
  DISK="${DISK:-$var_disk}"

  # Step 5: Bridge
  STEP=6
  BRIDGE=$(whiptail \
    --backtitle "$BACKTITLE" \
    --title "Network Bridge  [${STEP}/${MAX_STEP}]" \
    --ok-button "Next" --cancel-button "Back" \
    --inputbox "\nNetwork bridge (e.g. vmbr0):" 10 50 "$var_bridge" \
    3>&1 1>&2 2>&3) || { advanced_settings; return; }
  BRIDGE="${BRIDGE:-$var_bridge}"

  # Apply choices to globals
  NEXT_ID="$CT_ID"
  NSAPP="$CT_HOSTNAME"
  var_cpu="$CPU"
  var_ram="$RAM"
  var_disk="$DISK"
  var_bridge="$BRIDGE"
}

# ── Default or advanced prompt ────────────────────────────────────────────────
if whiptail \
  --backtitle "$BACKTITLE" \
  --title "Settings" \
  --yesno "\nUse default settings?\n\n  CT ID   : ${NEXT_ID} (next available)\n  Hostname: ${NSAPP}\n  CPU     : ${var_cpu} core(s)\n  RAM     : ${var_ram} MB\n  Disk    : ${var_disk} GB\n  Bridge  : ${var_bridge}\n  OS      : Debian ${var_version} (unprivileged)" \
  18 55; then
  : # accept defaults
else
  advanced_settings || msg_error "Installer cancelled."
fi

CTID="$NEXT_ID"

# ── ABS Credentials (required) ────────────────────────────────────────────────
ABS_HOST_VAL=""
ABS_TOKEN_VAL=""

whiptail \
  --backtitle "$BACKTITLE" \
  --title "ABS Credentials Required" \
  --ok-button "Continue" \
  --msgbox "\nAudiobookshelf credentials are required to continue.\n\nYou will need:\n  • Your ABS server URL\n  • Your personal ABS API token\n\nHow to find your API token:\n  1. Open your ABS instance in a browser\n  2. Click your username (top-right corner)\n  3. Select Edit Profile\n  4. Scroll down to the API Token section\n  5. Copy the token (long string starting with eyJ...)" \
  19 62

while [[ -z "$ABS_HOST_VAL" ]]; do
  ABS_HOST_VAL=$(whiptail \
    --backtitle "$BACKTITLE" \
    --title "ABS Server URL" \
    --ok-button "Next" \
    --inputbox "\nEnter the internal URL of your Audiobookshelf server.\nThis must be reachable from this Proxmox host.\n\nExample: http://192.168.1.100:13378" \
    13 62 "" \
    3>&1 1>&2 2>&3) || msg_error "Installer cancelled."
  [[ -z "$ABS_HOST_VAL" ]] && whiptail --backtitle "$BACKTITLE" --title "Required" \
    --msgbox "\nABS server URL cannot be empty." 8 40
done

while [[ -z "$ABS_TOKEN_VAL" ]]; do
  ABS_TOKEN_VAL=$(whiptail \
    --backtitle "$BACKTITLE" \
    --title "ABS API Token" \
    --ok-button "Done" \
    --passwordbox "\nPaste your ABS API token below.\nInput is hidden — paste works normally.\n" \
    11 62 \
    3>&1 1>&2 2>&3) || msg_error "Installer cancelled."
  [[ -z "$ABS_TOKEN_VAL" ]] && whiptail --backtitle "$BACKTITLE" --title "Required" \
    --msgbox "\nAPI token cannot be empty." 8 40
done

# ── Confirmation ──────────────────────────────────────────────────────────────
show_header
whiptail \
  --backtitle "$BACKTITLE" \
  --title "Confirm — Create Container ${CTID}" \
  --ok-button "Create" --cancel-button "Abort" \
  --yesno "\nThe following LXC container will be created:\n\n  CT ID   : ${CTID}\n  Hostname: ${NSAPP}\n  CPU     : ${var_cpu} core(s)\n  RAM     : ${var_ram} MB\n  Disk    : ${var_disk} GB\n  Bridge  : ${var_bridge}\n  OS      : Debian ${var_version} (unprivileged)\n  ABS host : ${ABS_HOST_VAL}\n  ABS token: configured\n\nProceed?" \
  22 62 || msg_error "Aborted by user."

show_header

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
  --net0     "name=eth0,bridge=${var_bridge},ip=dhcp" \
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
pct exec "$CTID" -- bash -c "VERBOSE=${VERBOSE} $(curl -fsSL "$INSTALL_URL")"
msg_ok "Install script complete"

# ── Write credentials and start service ──────────────────────────────────────
msg_info "Writing ABS credentials"
pct exec "$CTID" -- sed -i \
  -e "s|^ABS_HOST=.*|ABS_HOST=${ABS_HOST_VAL}|" \
  -e "s|^ABS_TOKEN=.*|ABS_TOKEN=${ABS_TOKEN_VAL}|" \
  /etc/audiobookshelf-now-playing.env
msg_ok "Credentials written"

msg_info "Starting service"
$STD pct exec "$CTID" -- systemctl start audiobookshelf-now-playing
msg_ok "Service started"

# ── Final output ──────────────────────────────────────────────────────────────
IP=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}')

printf "\n${GN}${CM}${APP} is live!${CL}\n"
printf "\n${YW}${INFO}Access the card at:${CL}\n"
printf "${TAB}${TAB}${BL}http://${IP}:8000/card${CL}\n"
printf "\n${YW}${INFO}To update in future:${CL}\n"
printf "${TAB}${TAB}${YW}CTID=${CTID} bash <(curl -fsSL https://raw.githubusercontent.com/StarlightDaemon/audiobookshelf-now-playing/main/deploy/ct/audiobookshelf-now-playing.sh) update${CL}\n\n"
