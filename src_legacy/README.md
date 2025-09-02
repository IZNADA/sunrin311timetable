# src_legacy (Deprecated)

이 디렉터리는 이전(레거시) 스크립트를 보존하기 위한 공간입니다. 현재 운영/실행 경로는 신규 구조를 따릅니다.

- 사용하지 마세요: `src_legacy/` 하위의 스크립트는 참고용으로만 남겨두었습니다.
- 권장 진입점: `python -m src.daemon --run-now` 또는 `./scripts/run_daemon.sh`
- 설정: 루트의 `.env`와 `requirements.txt`를 사용하세요.

대체 경로
- NEIS 연결 확인: `python src/check_neis.py`
- 실행(일회성): `python -m src.daemon --run-now`
- 데몬(포그라운드): `./scripts/run_daemon.sh`

