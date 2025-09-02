import os, requests
from normalize import normalize_subject

NEIS_HOST = "https://open.neis.go.kr/hub"
DEFAULT_TYPE = "json"

def _get_neis_key():
    return os.getenv("NEIS_KEY")

def _ensure_key():
    key = _get_neis_key()
    if not key:
        raise RuntimeError("NEIS_KEY가 .env에 없습니다. .env에 키를 추가하세요.")
    return key

def _check_head_ok(data: dict):
    for v in data.values():
        if isinstance(v, list) and v and isinstance(v[0], dict) and "head" in v[0]:
            head = v[0]["head"]
            for h in head:
                if isinstance(h, dict) and "RESULT" in h:
                    code = h["RESULT"].get("CODE")
                    msg  = h["RESULT"].get("MESSAGE")
                    if code and code != "INFO-000":
                        raise RuntimeError(f"NEIS API 오류: {code} - {msg}")
            return

def _get(path, params):
    # Ensure and use the NEIS key from environment
    key = _ensure_key()
    q = {"KEY": key, "Type": DEFAULT_TYPE, "pIndex": 1, "pSize": 100, **params}
    r = requests.get(f"{NEIS_HOST}/{path}", params=q, timeout=15)
    r.raise_for_status()
    data = r.json()
    _check_head_ok(data)
    return data

def find_school_codes(school_name, region_code=None):
    params = {"SCHUL_NM": school_name}
    if region_code:
        params["ATPT_OFCDC_SC_CODE"] = region_code
    data = _get("schoolInfo", params)
    rows = data.get("schoolInfo", [None, {"row": []}])[1]["row"]
    if not rows:
        raise RuntimeError(f"학교를 찾지 못했습니다: {school_name}")
    r0 = rows[0]
    return {
        "ATPT_OFCDC_SC_CODE": r0["ATPT_OFCDC_SC_CODE"],
        "ATPT_OFCDC_SC_NM": r0.get("ATPT_OFCDC_SC_NM"),
        "SD_SCHUL_CODE": r0["SD_SCHUL_CODE"],
        "SCHUL_NM": r0["SCHUL_NM"],
        "SCHUL_KND_SC_NM": r0.get("SCHUL_KND_SC_NM"),
    }

def list_classes(ATPT, SD_SCHUL_CODE, AY=None, GRADE=None):
    params = {"ATPT_OFCDC_SC_CODE": ATPT, "SD_SCHUL_CODE": SD_SCHUL_CODE}
    if AY: params["AY"] = AY
    if GRADE: params["GRADE"] = GRADE
    data = _get("classInfo", params)
    return data.get("classInfo", [None, {"row": []}])[1]["row"]

def get_timetable(school_level, ATPT, SD_SCHUL_CODE, yyyymmdd, grade, class_nm, AY=None, SEM=None):
    endpoint = {"els": "elsTimetable", "mis": "misTimetable", "his": "hisTimetable"}[school_level]
    params = {
        "ATPT_OFCDC_SC_CODE": ATPT,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "ALL_TI_YMD": yyyymmdd,
        "GRADE": str(grade),
        "CLASS_NM": str(class_nm),
    }
    if AY: params["AY"] = str(AY)
    if SEM: params["SEM"] = str(SEM)
    data = _get(endpoint, params)
    rows = data.get(endpoint, [None, {"row": []}])[1]["row"]
    rows.sort(key=lambda r: int(r.get("PERIO", 0)))
    result = []
    for r in rows:
        # Subject
        subject = normalize_subject(r.get("ITRT_CNTNT", "-"))

        # Room: try multiple possible keys; treat class number as non-room
        room_candidates = [
            r.get("CLRM_NM"),
            r.get("CLSRM_NM"),
            r.get("CLASSRM_NM"),
            r.get("ROOM_NM"),
        ]
        room_val = next((v for v in room_candidates if isinstance(v, str) and v.strip()), "")

        # Some APIs only provide CLASS_NM; avoid showing pure class number as room
        class_str = str(r.get("CLASS_NM") or class_nm or "").strip()
        def _digits(s):
            return "".join(ch for ch in str(s) if ch.isdigit())
        if room_val and _digits(room_val) and _digits(room_val) == _digits(class_str):
            room_val = ""

        result.append({
            "period": int(r.get("PERIO", 0)),
            "subject": subject,
            "room": room_val,
        })
    return result
