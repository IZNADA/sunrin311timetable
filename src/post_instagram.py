import os
import time
import requests
from .config import get_logger
from .token_manager import get_creds

# Use a single Graph API version across the project
GRAPH = "https://graph.facebook.com/v23.0"

log = get_logger(__name__)

TEST_MODE = os.getenv("POST_TEST_MODE", "true").lower() == "true"


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
    token, ig_user_id = get_creds()
    create_url = f"{GRAPH}/{ig_user_id}/media"
    data = {"image_url": image_url, "caption": caption, "access_token": token}
    j = _post_with_retry(create_url, data)
    creation_id = j.get("id")
    pub_url = f"{GRAPH}/{ig_user_id}/media_publish"
    j2 = _post_with_retry(pub_url, {"creation_id": creation_id, "access_token": token})
    return j2.get("id")


def edit_caption(media_id: str, new_caption: str) -> bool:
    if TEST_MODE:
        log.info("[TEST_MODE] Skipping caption edit. media_id=%s\nNew caption:\n%s", media_id, new_caption)
        return True
    token, _ = get_creds()
    url = f"{GRAPH}/{media_id}"
    _post_with_retry(url, {"caption": new_caption, "access_token": token})
    return True
