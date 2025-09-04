from PIL import Image, ImageDraw, ImageFont
import os
from .config import get_logger

log = get_logger(__name__)


def _try_truetype(path, size):
    try:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
    except Exception as e:
        log.debug("Font load failed for %s: %s", path, e)
    return None


def _pick_font(size, kind="regular"):
    """Pick a font with this priority:
    1) Env override (FONT_BOLD_PATH / FONT_REGULAR_PATH)
    2) Wanted Sans in assets (WantedSans-*.ttf/.otf)
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


def _draw_centered_text(draw: ImageDraw.ImageDraw, box, text, font, fill="black"):
    # box: (x0, y0, x1, y1)
    x0, y0, x1, y1 = box
    # Handle multiline
    lines = str(text).split("\n")
    line_heights = []
    line_widths = []
    total_h = 0
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_widths.append(w)
        line_heights.append(h)
        total_h += h
    # Add small line spacing
    total_h += max(0, len(lines) - 1) * 6
    cy = (y0 + y1) / 2 - total_h / 2
    for i, ln in enumerate(lines):
        w = line_widths[i]
        h = line_heights[i]
        cx = (x0 + x1) / 2 - w / 2
        draw.text((cx, cy), ln, fill=fill, font=font)
        cy += h + 6


def _build_rows(timetable):
    # Insert lunch after 4th period for visual layout
    rows = []
    for i, row in enumerate(timetable, start=1):
        rows.append({"label": f"{i}교시", "subject": (row.get("subject") or "-").strip()})
        if i == 4:
            rows.append({"label": "점심\n시간", "subject": ""})
    return rows


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
    # Choose template by period count (>=7 -> 7time)
    period_count = sum(1 for r in timetable if (r.get("subject") or "").strip())
    tpl_name = "assets/7time.png" if period_count >= 7 else "assets/6time.png"
    try:
        img = Image.open(tpl_name).convert("RGB")
    except Exception:
        # Fallback to plain white background
        img = Image.new("RGB", (1080, 1350), "white")
    d = ImageDraw.Draw(img)

    # Fonts
    title_font = _pick_font(64, kind="bold")
    date_font = _pick_font(40, kind="bold")
    label_font = _pick_font(60, kind="bold")
    subj_font = _pick_font(56, kind="regular")

    # Header texts
    if grade is not None and class_nm is not None:
        title_line = f"{grade}학년 {class_nm}반 시간표"
    else:
        title_line = "시간표"

    # Place header in two white ribbons (approximate boxes tuned for 1080x1350 asset)
    title_box = (100, 85, 650, 185)
    date_box = (650, 85, 1020, 185)
    _draw_centered_text(d, title_box, title_line, title_font, fill="black")
    _draw_centered_text(d, date_box, str(date_str), date_font, fill="black")

    # Rows
    rows = _build_rows(timetable)
    # Truncate/Pad depending on template type
    max_rows = 8 if "7time" in tpl_name else 7
    rows = rows[:max_rows]

    # Define column boxes
    left_x0, left_x1 = 95, 335
    right_x0, right_x1 = 365, 990

    # Vertical placement: tune base and gap to align with asset grid
    if "7time" in tpl_name:
        y_base, row_h = 360, 122  # 8 rows including lunch
    else:
        y_base, row_h = 360, 130  # 7 rows including lunch

    for idx, r in enumerate(rows):
        cy0 = y_base + idx * row_h
        box_left = (left_x0, cy0 - 55, left_x1, cy0 + 55)
        box_right = (right_x0, cy0 - 55, right_x1, cy0 + 55)

        label = r["label"]
        subj = r["subject"] or "수업 시간표"
        # Trim overly long subject
        if len(subj) > 18:
            subj = subj[:17] + "…"

        _draw_centered_text(d, box_left, label, label_font, fill="black")
        if "점심" not in label:
            _draw_centered_text(d, box_right, subj, subj_font, fill="black")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, quality=95)
    log.info("Saved image: %s (template=%s)", out_path, tpl_name)
    return out_path
