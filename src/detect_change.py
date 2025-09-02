import os, json, hashlib
STATE_PATH = "state/posted.json"

def calc_hash(obj):
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH) or ".", exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def record_post(date_key, post_id_or_marker, h):
    st = _load_state()
    st[date_key] = {"post_id": post_id_or_marker, "hash": h}
    _save_state(st)
