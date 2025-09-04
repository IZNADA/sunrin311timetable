import os
import time
import hmac
import hashlib
import requests
from .config import get_logger
from .token_manager import get_creds

log = get_logger(__name__)

TEST_MODE = os.getenv("POST_TEST_MODE", "true").lower() == "true"


def _ensure_creds():
    token, biz_id = get_creds()
    if not token or not biz_id:
        raise RuntimeError("Missing Instagram credentials")


def _post_with_retry(url: str, data: dict, attempts: int = 3, timeout: int = 30) -> dict:
    last_err = None
    for i in range(attempts):
        try:
            r = requests.post(url, data=data, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            last_err = e
            backoff = 2 ** i
            # Try to surface Graph error details when available
            status = getattr(e.response, "status_code", None)
            body = None
            try:
                if e.response is not None:
                    # Prefer JSON error details
                    body = e.response.json()
            except Exception:
                try:
                    body = e.response.text[:500] if e.response is not None else None
                except Exception:
                    body = None
            log.warning(
                "Graph API request failed (attempt %s/%s, status=%s): %s | details=%s",
                i + 1,
                attempts,
                status,
                e,
                body,
            )
            if i < attempts - 1:
                time.sleep(backoff)
    raise RuntimeError(f"Graph API request failed after {attempts} attempts: {last_err}")


def _append_appsecret_proof(params: dict, token: str) -> dict:
    """Append appsecret_proof when FB_APP_SECRET is provided."""
    app_secret = os.getenv("FB_APP_SECRET")
    if app_secret and token:
        try:
            digest = hmac.new(app_secret.encode("utf-8"), msg=token.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()
            params = dict(params)
            params["appsecret_proof"] = digest
        except Exception:
            pass
    return params


def upload_image_via_url(image_url: str, caption: str) -> str:
    if TEST_MODE:
        log.info("[TEST_MODE] Skipping upload. Caption preview:\n%s", caption)
        return "TEST_POST_ID"
    _ensure_creds()
    token, ig_user_id = get_creds()
    create_url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media"
    data = {"image_url": image_url, "caption": caption, "access_token": token}
    data = _append_appsecret_proof(data, token)
    j = _post_with_retry(create_url, data)
    creation_id = j.get("id")
    pub_url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media_publish"
    j2 = _post_with_retry(pub_url, _append_appsecret_proof({"creation_id": creation_id, "access_token": token}, token))
    return j2.get("id")


def edit_caption(media_id: str, new_caption: str) -> bool:
    if TEST_MODE:
        log.info("[TEST_MODE] Skipping caption edit. media_id=%s\nNew caption:\n%s", media_id, new_caption)
        return True
    _ensure_creds()
    token, _ = get_creds()
    url = f"https://graph.facebook.com/v21.0/{media_id}"
    _post_with_retry(url, _append_appsecret_proof({"caption": new_caption, "access_token": token}, token))
    return True
