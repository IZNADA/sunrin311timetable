#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="insta-timetable-daemon.service"
DEST_DIR="/etc/systemd/system"
PROJ_DIR="/opt/insta-timetable"

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

install -Dm644 systemd/${SERVICE_NAME} "${DEST_DIR}/${SERVICE_NAME}"
systemctl daemon-reload

timedatectl set-timezone Asia/Seoul || true

systemctl enable --now ${SERVICE_NAME}

echo "Installed and started ${SERVICE_NAME}. Logs: journalctl -u ${SERVICE_NAME} -n 200 --no-pager"

