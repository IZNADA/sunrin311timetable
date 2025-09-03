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

    raise RuntimeError(
        "No public image URL provider configured. Set IMAGE_URL_TEMPLATE or UPLOAD_PROVIDER=transfersh"
    )

