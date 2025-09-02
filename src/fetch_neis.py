import os
import json
import time
from typing import Dict, List, Optional
import requests

from .config import get_logger

log = get_logger(__name__)

NEIS_HOST = "https://open.neis.go.kr/hub"
DEFAULT_TYPE = "json"


def _get_neis_key() -> str:
    key = os.getenv("NEIS_KEY")
    if not key:
        raise RuntimeError("NEIS_KEY is not set in environment (.env)")
    return key


def _check_head_ok(data: dict):
    for v in data.values():
        if isinstance(v, list) and v and isinstance(v[0], dict) and "head" in v[0]:
            head = v[0]["head"]
            for h in head:
                if isinstance(h, dict) and "RESULT" in h:
                    code = h["RESULT"].get("CODE")
                    msg = h["RESULT"].get("MESSAGE")
                    if code and code != "INFO-000":
                        raise RuntimeError(f"NEIS API error: {code} - {msg}")
            return


def _request(path: str, params: dict, *, attempts: int = 3, timeout: int = 15) -> dict:
    key = _get_neis_key()
    session = requests.Session()
    q = {"KEY": key, "Type": DEFAULT_TYPE, "pIndex": 1, "pSize": 100, **params}
    url = f"{NEIS_HOST}/{path}"
    last_err = None
    for i in range(attempts):
        try:
            r = session.get(url, params=q, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            _check_head_ok(data)
            return data
        except Exception as e:
            last_err = e
            backoff = 2 ** i
            log.warning("NEIS request failed (attempt %s/%s): %s", i + 1, attempts, e)
            if i < attempts - 1:
                time.sleep(backoff)
    # After all attempts
    raise RuntimeError(f"NEIS request failed after {attempts} attempts: {last_err}")


def _normalize_subject(name: str) -> str:
    if not name:
        return "-"
    s = str(name).strip()
    # Strip common leading marks/spaces
    LEADING = set("*?-–—•··•[](){}·ㆍ··")
    i = 0
    while i < len(s) and (s[i] in LEADING or s[i].isspace()):
        i += 1
    s = s[i:]
    # Collapse whitespace
    s = " ".join(s.replace("\u00A0", " ").split())
    # Common typos
    low = s.lower()
    if low == "2d":
        s = "2D"
    if low == "3d":
        s = "3D"
    # Apply subject aliases (ENV inline JSON first, then file)
    try:
        inline = os.getenv("SUBJECT_ALIASES")
        aliases: Dict[str, str] = {}
        if inline:
            try:
                aliases = json.loads(inline)
            except Exception:
                aliases = {}
        if not aliases:
            path = os.getenv("SUBJECT_ALIASES_PATH", "data/subject_aliases.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        aliases = json.load(f)
                except Exception:
                    aliases = {}
        repl = aliases.get(s)
        if isinstance(repl, str) and repl.strip():
            return repl.strip()
    except Exception:
        pass
    return s


def find_school_codes(school_name: str, region_code: Optional[str] = None) -> Dict[str, str]:
    params = {"SCHUL_NM": school_name}
    if region_code:
        params["ATPT_OFCDC_SC_CODE"] = region_code
    data = _request("schoolInfo", params)
    rows = data.get("schoolInfo", [None, {"row": []}])[1]["row"]
    if not rows:
        raise RuntimeError(f"School not found: {school_name}")
    r0 = rows[0]
    return {
        "ATPT_OFCDC_SC_CODE": r0["ATPT_OFCDC_SC_CODE"],
        "ATPT_OFCDC_SC_NM": r0.get("ATPT_OFCDC_SC_NM"),
        "SD_SCHUL_CODE": r0["SD_SCHUL_CODE"],
        "SCHUL_NM": r0["SCHUL_NM"],
        "SCHUL_KND_SC_NM": r0.get("SCHUL_KND_SC_NM"),
    }


def list_classes(
    ATPT: str,
    SD_SCHUL_CODE: str,
    AY: Optional[str] = None,
    GRADE: Optional[str] = None,
) -> List[dict]:
    params = {"ATPT_OFCDC_SC_CODE": ATPT, "SD_SCHUL_CODE": SD_SCHUL_CODE}
    if AY:
        params["AY"] = AY
    if GRADE:
        params["GRADE"] = GRADE
    data = _request("classInfo", params)
    return data.get("classInfo", [None, {"row": []}])[1]["row"]


def get_timetable(
    school_level: str,
    ATPT: str,
    SD_SCHUL_CODE: str,
    yyyymmdd: str,
    grade: int,
    class_nm: str,
    AY: Optional[str] = None,
    SEM: Optional[str] = None,
) -> List[dict]:
    endpoint = {"els": "elsTimetable", "mis": "misTimetable", "his": "hisTimetable"}[school_level]
    params = {
        "ATPT_OFCDC_SC_CODE": ATPT,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "ALL_TI_YMD": yyyymmdd,
        "GRADE": str(grade),
        "CLASS_NM": str(class_nm),
    }
    if AY:
        params["AY"] = str(AY)
    if SEM:
        params["SEM"] = str(SEM)
    data = _request(endpoint, params)
    rows = data.get(endpoint, [None, {"row": []}])[1]["row"]
    rows.sort(key=lambda r: int(r.get("PERIO", 0)))

    # Build simplified rows
    result = []
    for r in rows:
        subject = _normalize_subject(r.get("ITRT_CNTNT", "-"))
        # Try room from multiple possible keys
        room_candidates = [
            r.get("CLRM_NM"),
            r.get("CLSRM_NM"),
            r.get("CLASSRM_NM"),
            r.get("ROOM_NM"),
        ]
        room_val = next((v for v in room_candidates if isinstance(v, str) and v.strip()), "")

        # Avoid displaying class number as room when not provided
        cls = str(r.get("CLASS_NM") or class_nm or "").strip()
        digits = lambda s: "".join(ch for ch in str(s) if ch.isdigit())
        if room_val and digits(room_val) and digits(room_val) == digits(cls):
            room_val = ""

        result.append(
            {
                "period": int(r.get("PERIO", 0)),
                "subject": subject,
                "room": room_val,
            }
        )
    return result
