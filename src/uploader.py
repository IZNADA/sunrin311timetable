import os
import uuid
import pathlib
import requests
from .config import get_logger

log = get_logger(__name__)


def _template_url_for(img_path: str) -> str:
    tmpl = os.getenv("IMAGE_URL_TEMPLATE", "").strip()
    if not tmpl:
        return ""
    p = pathlib.Path(img_path)
    return (
        tmpl.replace("{path}", str(p))
        .replace("{basename}", p.name)
        .replace("{stem}", p.stem)
        .replace("{ymd}", p.stem)
    )


def _upload_transfer_sh(img_path: str) -> str:
    """Upload an image to transfer.sh and return the public URL.

    Note: transfer.sh is a public, ephemeral file host. Use for testing or small scale only.
    """
    filename = pathlib.Path(img_path).name
    # add short random suffix to reduce collisions
    suf = uuid.uuid4().hex[:8]
    url = f"https://transfer.sh/{suf}-{filename}"
    with open(img_path, "rb") as f:
        r = requests.put(url, data=f, timeout=60)
        r.raise_for_status()
        final_url = r.text.strip()
        log.info("Uploaded image to transfer.sh: %s", final_url)
        return final_url


def get_public_image_url(img_path: str) -> str:
    """Return a public URL for the given image.

    Priority:
    1) IMAGE_URL_TEMPLATE env var
    2) UPLOAD_PROVIDER=transfersh
    """
    u = _template_url_for(img_path)
    if u:
        return u

    provider = os.getenv("UPLOAD_PROVIDER", "").strip().lower()
    if provider == "transfersh":
        return _upload_transfer_sh(img_path)
    if provider in ("catbox", "catbox.moe"):
        # Public host that returns a direct URL
        with open(img_path, "rb") as f:
            files = {"fileToUpload": (pathlib.Path(img_path).name, f, "image/jpeg")}
            data = {"reqtype": "fileupload"}
            r = requests.post("https://catbox.moe/user/api.php", data=data, files=files, timeout=60)
            r.raise_for_status()
            url = r.text.strip()
            log.info("Uploaded image to catbox: %s", url)
            return url

    # Auto fallback: try transfer.sh then catbox
    try:
        return _upload_transfer_sh(img_path)
    except Exception as e:
        log.warning("transfer.sh failed: %s; falling back to catbox", e)
        with open(img_path, "rb") as f:
            files = {"fileToUpload": (pathlib.Path(img_path).name, f, "image/jpeg")}
            data = {"reqtype": "fileupload"}
            r = requests.post("https://catbox.moe/user/api.php", data=data, files=files, timeout=60)
            r.raise_for_status()
            url = r.text.strip()
            log.info("Uploaded image to catbox: %s", url)
            return url
