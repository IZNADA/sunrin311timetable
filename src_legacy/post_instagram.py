import os, requests

TOKEN = os.getenv("IG_PAGE_ACCESS_TOKEN")
BIZ_ID = os.getenv("IG_BUSINESS_ID")
TEST_MODE = (os.getenv("POST_TEST_MODE", "true").lower() == "true")

def _ensure_creds():
    if not TOKEN or not BIZ_ID:
        raise RuntimeError("IG_PAGE_ACCESS_TOKEN 또는 IG_BUSINESS_ID가 .env에 없습니다.")

def upload_image_via_url(image_url, caption):
    if TEST_MODE:
        print("[TEST_MODE] 업로드 생략. caption 미리보기:\n", caption)
        return "TEST_POST_ID"
    _ensure_creds()
    create_url = f"https://graph.facebook.com/v21.0/{BIZ_ID}/media"
    r = requests.post(create_url, data={"image_url": image_url, "caption": caption, "access_token": TOKEN}, timeout=30)
    r.raise_for_status()
    creation_id = r.json().get("id")
    pub_url = f"https://graph.facebook.com/v21.0/{BIZ_ID}/media_publish"
    p = requests.post(pub_url, data={"creation_id": creation_id, "access_token": TOKEN}, timeout=30)
    p.raise_for_status()
    return p.json().get("id")

def edit_caption(media_id, new_caption):
    if TEST_MODE:
        print(f"[TEST_MODE] 캡션 수정 생략. 대상: {media_id}\n새 캡션:\n{new_caption}")
        return True
    _ensure_creds()
    url = f"https://graph.facebook.com/v21.0/{media_id}"
    r = requests.post(url, data={"caption": new_caption, "access_token": TOKEN}, timeout=30)
    r.raise_for_status()
    return True
