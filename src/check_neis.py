import os, requests
from dotenv import load_dotenv
load_dotenv()
KEY = os.getenv("NEIS_KEY")
if not KEY:
    raise SystemExit("NEIS_KEY가 .env에 없습니다.")
url = "https://open.neis.go.kr/hub/schoolInfo"
params = {"KEY": KEY, "Type": "json", "pIndex": 1, "pSize": 1, "SCHUL_NM": "선린인터넷고등학교"}
r = requests.get(url, params=params, timeout=15)
r.raise_for_status()
data = r.json()
ok = False
for v in data.values():
    if isinstance(v, list) and v and isinstance(v[0], dict) and "head" in v[0]:
        head = v[0]["head"]
        for h in head:
            if isinstance(h, dict) and h.get("RESULT", {}).get("CODE") == "INFO-000":
                ok = True
                break
print("NEIS 연결 성공 ✅" if ok else f"응답 확인 필요 ❗ data={data}")
