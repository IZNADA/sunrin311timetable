#!/usr/bin/env bash
set -euo pipefail

# Arch 패키지 설치
sudo pacman -Sy --noconfirm python python-pip git noto-fonts-cjk

# 프로젝트 디렉토리 준비(배포 시 /opt/insta-timetable로 복사한다고 가정)
PROJ_DIR="/opt/insta-timetable"
if [ ! -d "$PROJ_DIR" ]; then
  echo "프로젝트 디렉토리가 $PROJ_DIR 에 존재해야 합니다. rsync 또는 scp로 복사 후 다시 실행하세요."
  exit 1
fi

cd "$PROJ_DIR"
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 권한 정리
chmod 600 .env || true
mkdir -p out state || true

# 기본 테스트
python src/check_neis.py || (echo "NEIS 연결 실패"; exit 1)
echo "설치 완료"
