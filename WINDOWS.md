# Windows 빠른 시작

이 문서는 Windows에서 바로 실행할 수 있도록 Git, Python venv, .env 설정, 실행/스케줄링 체크리스트를 정리합니다.

> 중요: 레거시 코드 안내
> 
레거시(`src_legacy/`)는 제거되었습니다. 실행은 `src/daemon.py` 기준입니다.

## 필수 설치

- Git for Windows: 최신 버전
- Python: 3.10 이상 (Windows용 Python Launcher 포함 권장)
- 폰트: Wanted Sans는 리포 `assets/`에 포함(추가 설치 불필요)

## 코드 가져오기

```powershell
git clone https://github.com/IZNADA/sunrin311timetable.git
cd sunrin311timetable
git pull
```

## 가상환경 + 패키지

- PowerShell
```powershell
py -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

- CMD
```cmd
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

- 확인
```powershell
python -c "import PIL,requests,dotenv,pytz;print('ok')"
```

## 환경변수(.env)

```powershell
copy .env.example .env
```

- 필수 값
  - `NEIS_KEY`: 실제 키 입력
  - `SCHOOL_NAME=선린인터넷고등학교`
  - `SCHOOL_LEVEL=his`, `GRADE=3`, `CLASS_NM=11`
  - `POST_TEST_MODE=true` (기본: 실제 업로드 안 함)
- 선택 값
  - `FONT_REGULAR_PATH`, `FONT_BOLD_PATH` (기본은 리포 내 Wanted Sans 자동 사용)
  - `SUBJECT_ALIASES` 또는 `SUBJECT_ALIASES_PATH` (과목 치환)

## 실행(Windows 경로)

```powershell
# NEIS 연결 확인
python src\check_neis.py

# 바로 한 번 실행(이미지 생성 + 업로드)
py -m src.daemon --run-now
```

## 산출물/미리보기

- 이미지: `out\YYYYMMDD.jpg`
- 상태: `state\posted.json`
- (선택) 미리보기 서버는 별도 제공하지 않습니다.

## 스케줄링(작업 스케줄러, 선택)

- 작업 디렉터리 보장을 위한 간단 .cmd 래퍼 포함됨
  - `run_daily.cmd` (daemon --run-now 호출)
  - `run_update.cmd` (동일 실행)

- 작업 등록 예시
```cmd
REM 매일 07:00 실행
schtasks /Create /SC DAILY /ST 07:00 /TN InstaTimetableDaily /TR "C:\\path\\to\\sunrin311timetable\\run_daily.cmd"

REM 30분마다 실행
schtasks /Create /SC MINUTE /MO 30 /TN InstaTimetableUpdate /TR "C:\\path\\to\\sunrin311timetable\\run_update.cmd"
```

## Git/PAT

```powershell
git add -A && git commit -m "메시지" && git push
```

- HTTPS 푸시: Username은 `IZNADA`, Password는 발급한 Fine‑grained 토큰(PAT)

## Windows 흔한 이슈

- PowerShell 실행 정책: 필요 시 관리자 PowerShell에서 실행
  - `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
- 경로 구분: `\` 사용, `.ps1`는 PowerShell, `.cmd`는 CMD
- 작업 디렉터리: 스케줄러에선 `.cmd` 내부 `cd /d`로 보장 권장
