import os
import json
import time
from typing import Tuple

import requests

from .config import get_logger

log = get_logger(__name__)

GRAPH = "https://graph.facebook.com/v21.0"
STATE_DIR = os.getenv("STATE_DIR", "state")
TOKEN_STATE_PATH = os.path.join(STATE_DIR, "token.json")


def _load_state() -> dict:
    try:
        if os.path.exists(TOKEN_STATE_PATH):
            with open(TOKEN_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        log.warning("Failed to load token state: %s", e)
    return {}


def _save_state(state: dict) -> None:
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(TOKEN_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning("Failed to save token state: %s", e)


def _get(key: str) -> str:
    return (os.getenv(key) or "").strip()


def _now() -> int:
    return int(time.time())


def _debug_token(user_token: str, app_id: str, app_secret: str) -> dict:
    try:
        app_access = f"{app_id}|{app_secret}"
        r = requests.get(
            f"{GRAPH}/debug_token",
            params={"input_token": user_token, "access_token": app_access},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("data", {})
    except Exception as e:
        log.warning("debug_token failed: %s", e)
        return {}


def _exchange_long_lived(user_token: str, app_id: str, app_secret: str) -> str:
    r = requests.get(
        f"{GRAPH}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": user_token,
        },
        timeout=30,
    )
    r.raise_for_status()
    return (r.json() or {}).get("access_token", "")


def _get_page_token(user_token: str, page_id: str) -> str:
    r = requests.get(
        f"{GRAPH}/{page_id}",
        params={"fields": "access_token", "access_token": user_token},
        timeout=30,
    )
    r.raise_for_status()
    return (r.json() or {}).get("access_token", "")


def _get_ig_user_id(user_token: str, page_id: str) -> str:
    r = requests.get(
        f"{GRAPH}/{page_id}",
        params={"fields": "instagram_business_account{id}", "access_token": user_token},
        timeout=30,
    )
    r.raise_for_status()
    return ((r.json() or {}).get("instagram_business_account") or {}).get("id", "")


def get_creds() -> Tuple[str, str]:
    """Return (access_token, ig_user_id) for posting.

    Modes:
    - Fixed: IG_PAGE_ACCESS_TOKEN + IG_BUSINESS_ID
    - Derived (auto): IG_USER_ACCESS_TOKEN + PAGE_ID [+ FB_APP_ID/FB_APP_SECRET for refresh]
    """
    # Fixed token mode
    fixed_token = _get("IG_PAGE_ACCESS_TOKEN")
    fixed_ig = _get("IG_BUSINESS_ID")
    if fixed_token and fixed_ig:
        return fixed_token, fixed_ig

    # Auto-derive mode
    st = _load_state()
    user_token = st.get("user_token") or _get("IG_USER_ACCESS_TOKEN")
    page_id = _get("PAGE_ID")
    if not (user_token and page_id):
        raise RuntimeError("Missing creds: provide IG_PAGE_ACCESS_TOKEN+IG_BUSINESS_ID, or IG_USER_ACCESS_TOKEN+PAGE_ID")

    app_id = _get("FB_APP_ID")
    app_secret = _get("FB_APP_SECRET")
    try:
        if app_id and app_secret:
            info = _debug_token(user_token, app_id, app_secret)
            exp = int(info.get("expires_at") or 0)
            if exp:
                days_left = (exp - _now()) / 86400
                threshold = float(_get("TOKEN_REFRESH_THRESHOLD_DAYS") or 7)
                if days_left < threshold:
                    new_user = _exchange_long_lived(user_token, app_id, app_secret)
                    if new_user:
                        user_token = new_user
                        st["user_token"] = new_user
                        _save_state(st)
                        log.info("Refreshed long-lived user token (days_left=%.1f)", days_left)
    except Exception as e:
        log.warning("Token refresh check failed: %s", e)

    page_token = _get_page_token(user_token, page_id)
    ig_user = _get_ig_user_id(user_token, page_id)
    if not (page_token and ig_user):
        raise RuntimeError("Failed to derive page token or IG user id. Check PAGE_ID linkage and token scopes.")
    return page_token, ig_user

