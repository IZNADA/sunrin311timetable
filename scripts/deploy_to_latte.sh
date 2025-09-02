#!/usr/bin/env bash
set -euo pipefail
LATTE_USER="${LATTE_USER:-root}"
LATTE_HOST="${LATTE_HOST:-192.168.0.50}"   # 라떼판다 IP로 변경
DEST="/opt/insta-timetable"

rsync -avz --delete --exclude ".git" --exclude "__pycache__" ./ "$LATTE_USER@$LATTE_HOST:$DEST/"

ssh "$LATTE_USER@$LATTE_HOST" "sudo chmod +x $DEST/scripts/setup_arch.sh && sudo $DEST/scripts/setup_arch.sh && \
  sudo cp $DEST/systemd/*.service /etc/systemd/system/ && \
  sudo cp $DEST/systemd/*.timer /etc/systemd/system/ && \
  sudo systemctl daemon-reload && \
  sudo timedatectl set-timezone Asia/Tokyo && \
  sudo systemctl enable --now insta-timetable-daily.timer && \
  sudo systemctl enable --now insta-timetable-update.timer"

echo "배포/설치 완료. 로그:"
ssh "$LATTE_USER@$LATTE_HOST" "systemctl status insta-timetable-daily.timer --no-pager; journalctl -u insta-timetable-daily.service -n 50 --no-pager"
