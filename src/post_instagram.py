import os
import time
import requests
from .config import get_logger

log = get_logger(__name__)

TOKEN = os.getenv("IG_PAGE_ACCESS_TOKEN")
BIZ_ID = os.getenv("IG_BUSINESS_ID")
TEST_MODE = os.getenv("POST_TEST_MODE", "true").lower() == "true"


def _ensure_creds():
    if not TOKEN or not BIZ_ID:
        raise RuntimeError("IG_PAGE_ACCESS_TOKEN or IG_BUSINESS_ID is not set in .env")


def _post_with_retry(url: str, data: dict, attempts: int = 3, timeout: int = 30) -> dict:
    last_err = None
    for i in range(attempts):
        try:
            r = requests.post(url, data=data, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            backoff = 2 ** i
            log.warning("Graph API request failed (attempt %s/%s): %s", i + 1, attempts, e)
            if i < attempts - 1:
                time.sleep(backoff)
    raise RuntimeError(f"Graph API request failed after {attempts} attempts: {last_err}")


def upload_image_via_url(image_url: str, caption: str) -> str:
    if TEST_MODE:
        log.info("[TEST_MODE] Skipping upload. Caption preview:\n%s", caption)
        return "TEST_POST_ID"
    _ensure_creds()
    create_url = f"https://graph.facebook.com/v21.0/{BIZ_ID}/media"
    data = {"image_url": image_url, "caption": caption, "access_token": TOKEN}
    j = _post_with_retry(create_url, data)
    creation_id = j.get("id")
    pub_url = f"https://graph.facebook.com/v21.0/{BIZ_ID}/media_publish"
    j2 = _post_with_retry(pub_url, {"creation_id": creation_id, "access_token": TOKEN})
    return j2.get("id")


def edit_caption(media_id: str, new_caption: str) -> bool:
    if TEST_MODE:
        log.info("[TEST_MODE] Skipping caption edit. media_id=%s\nNew caption:\n%s", media_id, new_caption)
        return True
    _ensure_creds()
    url = f"https://graph.facebook.com/v21.0/{media_id}"
    _post_with_retry(url, {"caption": new_caption, "access_token": TOKEN})
    return True

