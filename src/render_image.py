"""
Image rendering functionality for timetable data.
"""

from PIL import Image, ImageDraw, ImageFont
import os


def _try_truetype(path, size):
    try:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
    except Exception:
        pass
    return None


def _pick_font(size, kind="regular"):
    """Pick a font with this priority:
    1) Env override (FONT_BOLD_PATH / FONT_REGULAR_PATH)
    2) Wanted Sans in assets (WantedSans-*.ttf or .otf)
    3) NotoSansKR in assets
    4) Default PIL font
    """
    env_key = "FONT_BOLD_PATH" if kind == "bold" else "FONT_REGULAR_PATH"
    env_path = os.getenv(env_key)
    if env_path:
        f = _try_truetype(env_path, size)
        if f:
            return f

    wanted_candidates = [
        "assets/WantedSans-Bold.ttf" if kind == "bold" else "assets/WantedSans-Regular.ttf",
        "assets/WantedSans-Bold.otf" if kind == "bold" else "assets/WantedSans-Regular.otf",
        # Some distributions use space in name
        "assets/Wanted Sans Bold.ttf" if kind == "bold" else "assets/Wanted Sans Regular.ttf",
        "assets/Wanted Sans Bold.otf" if kind == "bold" else "assets/Wanted Sans Regular.otf",
    ]
    for p in wanted_candidates:
        f = _try_truetype(p, size)
        if f:
            return f

    noto_candidates = [
        "assets/NotoSansKR-Bold.ttf" if kind == "bold" else "assets/NotoSansKR-Regular.ttf",
        "assets/NotoSansKR-Black.ttf" if kind == "bold" else "assets/NotoSansKR-Medium.ttf",
    ]
    for p in noto_candidates:
        f = _try_truetype(p, size)
        if f:
            return f

    return ImageFont.load_default()


def render_timetable_image(
    date_str,
    timetable,
    out_path,
    brand_color="#2A6CF0",
    *,
    school_name=None,
    grade=None,
    class_nm=None,
):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    bold_font = _pick_font(72, kind="bold")
    reg_font = _pick_font(44, kind="regular")
    small_f = _pick_font(36, kind="regular")

    d.rectangle((0, 0, W, 220), fill=brand_color)

    # Title first line: "3학년 11반 시간표"
    if grade is not None and class_nm is not None:
        title_line = f"{grade}학년 {class_nm}반 시간표"
    else:
        title_line = "시간표"
    d.text((60, 60), title_line, fill="white", font=bold_font)

    # Second line: date on a new line
    d.text((60, 140), f"{date_str}", fill="white", font=reg_font)

    y = 260
    line_gap = 90
    side = 80
    for i, row in enumerate(timetable, start=1):
        subject = (row.get("subject") or "-").strip()
        if len(subject) > 18:
            subject = subject[:17] + "…"
        text = f"{i}교시  {subject}"
        d.text((side, y), text, fill="black", font=reg_font)
        y += line_gap
        d.line((side, y, W - side, y), fill="#eaeaea", width=3)
        y += 20

    # Footer removed per request

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, quality=95)
    return out_path
