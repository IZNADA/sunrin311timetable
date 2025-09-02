# sunrin311timetable

선린 25학년도 3-11 학급의 시간표를 매일 7시마다 인스타그램에 자동 업로드하는 프로젝트.

## 목적
NEIS(나이스) Open API로 ‘선린인터넷고등학교 3학년 11반’의 해당 날짜 시간표를 조회하여 인스타그램 규격(1080x1350) 이미지로 생성하고, (테스트 모드) 업로드 및 변경 감지(정정 게시)를 준비합니다.

## 로컬 실행

### 1) 가상환경 생성 및 패키지 설치
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2) 환경변수 설정
```bash
cp .env.example .env
# .env 파일에 실제 NEIS_KEY 입력
```

#### 폰트 설정 (원티드 산스)
- 기본 내장 폰트는 NotoSansKR입니다. 원티드 산스를 쓰려면 아래 중 하나를 선택하세요.
  1) `assets/`에 폰트 파일 추가: `assets/WantedSans-Regular.ttf`, `assets/WantedSans-Bold.ttf`
  2) 또는 `.env`에 경로 지정:
     - `FONT_REGULAR_PATH=/path/to/WantedSans-Regular.ttf`
     - `FONT_BOLD_PATH=/path/to/WantedSans-Bold.ttf`

렌더러는 순서대로 (ENV 지정 → assets의 Wanted Sans → assets의 NotoSansKR → 기본 폰트) 로 폰트를 선택합니다.

#### 과목명 정규화/치환
- 과목명 앞의 불릿/별표(예: `*`, `•`, `★`)는 자동 제거됩니다.
- 과목명 치환은 `data/subject_aliases.json`에서 설정할 수 있습니다.
  - 예) `"2D 그래픽제작": "광고 콘텐츠"`, `"인쇄편집": "광고 콘텐츠"`, `"진로활동": "자율"`
  - ENV로도 지정 가능: `SUBJECT_ALIASES='{"원본":"치환"}'`

### 3) 실행
```bash
# NEIS 연결 확인
python src/check_neis.py

# 3학년 반 목록 확인
python src/list_classes.py

# 오늘 시간표 이미지 생성(NEIS)
python src/local_demo_neis.py

# CSV 데모
python src/local_demo.py

# (테스트모드) 매일 게시 로직
python src/main_daily.py

# (테스트모드) 변경 감지
python src/main_update.py
```

생성되는 이미지 상단 헤더는 다음 형식입니다.
- 1줄째: `3학년 11반 시간표`
- 2줄째: `YYYY-MM-DD (한글 요일)`

## 특정 날짜 이미지 생성(NEIS)
```bash
TARGET_DATE_YYYYMMDD=20250901 python src/local_demo_neis.py
```

## Arch 배포/운영 (systemd)

### 자동 배포 (macOS에서)
```bash
chmod +x scripts/deploy_to_latte.sh
LATTE_USER=root LATTE_HOST=<라떼판다_IP> ./scripts/deploy_to_latte.sh
```

### 수동 설치 (라떼판다에서)
```bash
sudo chmod +x scripts/setup_arch.sh
sudo ./scripts/setup_arch.sh
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now insta-timetable-daily.timer
sudo systemctl enable --now insta-timetable-update.timer
```

### 로그 확인
```bash
journalctl -u insta-timetable-daily.service -n 200 --no-pager
journalctl -u insta-timetable-update.service -n 200 --no-pager
```

## 운용 전환 (인스타 실게시)
1. IG 비즈/크리에이터 전환 + 페북 페이지 연결
2. `.env`에 `IG_PAGE_ACCESS_TOKEN`, `IG_BUSINESS_ID` 설정
3. `POST_TEST_MODE=false`로 전환
4. 이미지 공개 URL 업로더 연결 후 `image_url` 변수 채움
5. systemd 재시작


## Daemon (APScheduler, Asia/Seoul)

- Timezone is fixed to Asia/Seoul in code.
- Foreground quick test: `./scripts/run_daemon.sh --run-now`
- Start as a daemon with systemd: `sudo ./scripts/install_systemd.sh`
- Logs: `journalctl -u insta-timetable-daemon.service -n 200 --no-pager`
