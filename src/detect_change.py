import os
import json
import hashlib
from typing import Dict, Any
from .config import get_logger

log = get_logger(__name__)

STATE_PATH = os.getenv("STATE_PATH", "state/posted.json")


def calc_hash(obj: Any) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning("Failed to load state file, starting fresh: %s", e)
            return {}
    return {}


def _save_state(state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(STATE_PATH) or ".", exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def record_post(date_key: str, post_id_or_marker: str, h: str) -> None:
    st = _load_state()
    st[date_key] = {"post_id": post_id_or_marker, "hash": h}
    _save_state(st)


def last_hash(date_key: str) -> str:
    st = _load_state()
    v = st.get(date_key)
    if isinstance(v, dict):
        return v.get("hash")
    return ""

