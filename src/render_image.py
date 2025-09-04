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
        # Allow override: LUNCH_AFTER_PERIOD env (default 4)
        lunch_after = int(os.getenv("LUNCH_AFTER_PERIOD", "4") or 4)
        if i == lunch_after:
            rows.append({"label": "점심\n시간", "subject": ""})
    return rows


def _env_box(key: str, default):
    s = os.getenv(key)
    if s:
        try:
            x0, y0, x1, y1 = map(int, s.split(","))
            return (x0, y0, x1, y1)
        except Exception:
            pass
    return default


def _env_int(key: str, default: int) -> int:
    try:
        v = os.getenv(key)
        return int(v) if v not in (None, "") else default
    except Exception:
        return default


def _env_xy(key: str):
    s = os.getenv(key)
    if s:
        try:
            x, y = map(int, s.split(","))
            return (x, y)
        except Exception:
            return None
    return None


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
    date_font = _pick_font(32, kind="bold")
    label_font = _pick_font(60, kind="bold")
    subj_font = _pick_font(48, kind="bold")

    # Header text: date placement
    # Options (env overrides):
    #  - DATE_BOX_6TIME / DATE_BOX_7TIME = "x0,y0,x1,y1" (legacy box-centering)
    #  - DATE_BOX_OFFSET_Y[_6TIME|_7TIME] = int (nudge Y)
    #  - DATE_CENTER_Y[_6TIME|_7TIME] = int (force vertical center in the box)
    #  - DATE_ANCHOR_XY[_6TIME|_7TIME] = "x,y" (absolute anchor point)
    #  - DATE_ANCHOR_MODE[_6TIME|_7TIME] = topleft|center|center_top (default: topleft)
    # Slightly lowered default box to better match left title area when box mode is used.
    default_date_box = (640, 110, 1015, 210)

    # Resolve per-template envs
    is7 = "7time" in tpl_name
    date_box = _env_box("DATE_BOX_7TIME" if is7 else "DATE_BOX_6TIME", default_date_box)
    offset_y = int(os.getenv("DATE_BOX_OFFSET_Y_7TIME" if is7 else "DATE_BOX_OFFSET_Y_6TIME", os.getenv("DATE_BOX_OFFSET_Y", "0") or 0))
    center_y_env = os.getenv("DATE_CENTER_Y_7TIME" if is7 else "DATE_CENTER_Y_6TIME", os.getenv("DATE_CENTER_Y"))

    # Anchor controls
    anchor_xy_env = os.getenv("DATE_ANCHOR_XY_7TIME" if is7 else "DATE_ANCHOR_XY_6TIME", os.getenv("DATE_ANCHOR_XY"))
    anchor_mode = os.getenv("DATE_ANCHOR_MODE_7TIME" if is7 else "DATE_ANCHOR_MODE_6TIME", os.getenv("DATE_ANCHOR_MODE", "topleft")).lower()

    if anchor_xy_env:
        # Absolute-anchored drawing
        try:
            ax, ay = map(int, anchor_xy_env.split(","))
            bbox = d.textbbox((0, 0), str(date_str), font=date_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            if anchor_mode in ("center", "center_center"):
                px, py = ax - tw // 2, ay - th // 2
            elif anchor_mode in ("center_top", "topcenter", "top_center"):
                px, py = ax - tw // 2, ay
            elif anchor_mode in ("left_center", "center_left"):
                px, py = ax, ay - th // 2
            else:  # topleft
                px, py = ax, ay
            # Optional horizontal align within width (when using top-based modes)
            date_align = (os.getenv("DATE_ALIGN", "left") or "left").lower()
            if date_align != "left":
                align_w = _env_int("DATE_ALIGN_W_7TIME" if is7 else "DATE_ALIGN_W_6TIME", _env_int("DATE_ALIGN_W", 0))
                align_x1 = _env_int("DATE_ALIGN_X1_7TIME" if is7 else "DATE_ALIGN_X1_6TIME", _env_int("DATE_ALIGN_X1", 0))
                width = align_w if align_w > 0 else (align_x1 - ax if align_x1 > 0 else None)
                if width and width > 0:
                    if date_align == "center":
                        px = ax + (width - tw) // 2
                    elif date_align == "right":
                        px = ax + (width - tw)
            d.text((px, py), str(date_str), fill="black", font=date_font)
            # Optional debug marker
            if (os.getenv("RENDER_DEBUG_BOXES", "false").lower() == "true"):
                d.rectangle((px, py, px + tw, py + th), outline="#ff00ff", width=2)
        except Exception:
            # Fallback to box-based centering if parsing fails
            x0, y0, x1, y1 = date_box
            if center_y_env not in (None, ""):
                try:
                    cy = int(center_y_env)
                    half = (y1 - y0) // 2
                    y0, y1 = cy - half, cy + half
                except Exception:
                    pass
            if offset_y:
                y0 += offset_y
                y1 += offset_y
            _draw_centered_text(d, (x0, y0, x1, y1), str(date_str), date_font, fill="black")
    else:
        # Box-based centering path
        x0, y0, x1, y1 = date_box
        if center_y_env not in (None, ""):
            try:
                cy = int(center_y_env)
                half = (y1 - y0) // 2
                y0, y1 = cy - half, cy + half
            except Exception:
                pass
        if offset_y:
            y0 += offset_y
            y1 += offset_y
        date_box = (x0, y0, x1, y1)
        _draw_centered_text(d, date_box, str(date_str), date_font, fill="black")

    # Rows
    rows = _build_rows(timetable)
    # Truncate/Pad depending on template type
    max_rows = 8 if "7time" in tpl_name else 7
    rows = rows[:max_rows]

    # Subject placement supports two modes:
    # 1) Anchor mode: absolute (x,y) per first period + uniform DY spacing; optional separate anchor/dy after lunch
    # 2) Box mode: legacy box-centered drawing using template-aligned boxes
    is7 = "7time" in tpl_name

    # Anchor mode parameters (per-template override → common)
    subj_anchor = _env_xy("SUBJECT_ANCHOR_XY_7TIME" if is7 else "SUBJECT_ANCHOR_XY_6TIME") or _env_xy("SUBJECT_ANCHOR_XY")
    subj_anchor_after = _env_xy("SUBJECT_ANCHOR_AFTER_LUNCH_XY_7TIME" if is7 else "SUBJECT_ANCHOR_AFTER_LUNCH_XY") or _env_xy("SUBJECT_ANCHOR_AFTER_LUNCH_XY")
    subj_dy = _env_int("SUBJECT_ROW_DY_7TIME" if is7 else "SUBJECT_ROW_DY_6TIME", _env_int("SUBJECT_ROW_DY", 0))
    subj_dy_after = _env_int("SUBJECT_ROW_DY_AFTER_LUNCH_7TIME" if is7 else "SUBJECT_ROW_DY_AFTER_LUNCH_6TIME", _env_int("SUBJECT_ROW_DY_AFTER_LUNCH", subj_dy or 0))
    subj_anchor_mode = (os.getenv("SUBJECT_ANCHOR_MODE_7TIME" if is7 else "SUBJECT_ANCHOR_MODE", os.getenv("SUBJECT_ANCHOR_MODE", "topleft")) or "topleft").lower()
    subj_align = (os.getenv("SUBJECT_ALIGN_7TIME" if is7 else "SUBJECT_ALIGN_6TIME", os.getenv("SUBJECT_ALIGN", "left")) or "left").lower()
    subj_align_w = _env_int("SUBJECT_ALIGN_W_7TIME" if is7 else "SUBJECT_ALIGN_W_6TIME", _env_int("SUBJECT_ALIGN_W", 0))
    subj_align_x1 = _env_int("SUBJECT_ALIGN_X1_7TIME" if is7 else "SUBJECT_ALIGN_X1_6TIME", _env_int("SUBJECT_ALIGN_X1", 0))

    lunch_after = int(os.getenv("LUNCH_AFTER_PERIOD", "4") or 4)

    if subj_anchor:
        # Anchor-based absolute placement
        period_idx = 0  # counts non-lunch periods (1-based when incremented)
        after_lunch_flag = False
        for r in rows:
            label = r["label"]
            subj = r["subject"] or "수업 시간표"
            if len(subj) > 18:
                subj = subj[:17] + "…"

            if "점심" in label:
                after_lunch_flag = True
                continue

            period_idx += 1

            # Choose base and dy depending on lunch boundary
            if after_lunch_flag and subj_anchor_after:
                base_x, base_y = subj_anchor_after
                base_idx = lunch_after + 1
                dy_use = subj_dy_after or subj_dy or 0
            else:
                base_x, base_y = subj_anchor
                base_idx = 1
                dy_use = subj_dy or 0

            px = base_x
            py = base_y + dy_use * (period_idx - base_idx)

            # Render at anchor
            bbox = d.textbbox((0, 0), subj, font=subj_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            if subj_anchor_mode in ("center", "center_center"):
                tx = px - tw // 2
                ty = py - th // 2
            elif subj_anchor_mode in ("center_top", "topcenter", "top_center"):
                tx = px - tw // 2
                ty = py
            elif subj_anchor_mode in ("left_center", "center_left"):
                tx = px
                ty = py - th // 2
            else:  # topleft
                tx, ty = px, py

            # Horizontal align within width from anchor if requested
            if subj_align != "left":
                width = subj_align_w if subj_align_w > 0 else (subj_align_x1 - px if subj_align_x1 > 0 else None)
                if width and width > 0:
                    if subj_align == "center":
                        tx = px + (width - tw) // 2
                    elif subj_align == "right":
                        tx = px + (width - tw)

            d.text((tx, ty), subj, fill="black", font=subj_font)

            if (os.getenv("RENDER_DEBUG_BOXES", "false").lower() == "true"):
                bbox = d.textbbox((tx, ty), subj, font=subj_font)
                d.rectangle(bbox, outline="#0000ff", width=1)
    else:
        # Box-centered legacy placement
        if is7:
            right_x0 = _env_int("SUBJECT_X0_7TIME", _env_int("SUBJECT_X0", 365))
            right_x1 = _env_int("SUBJECT_X1_7TIME", _env_int("SUBJECT_X1", 990))
            y_base = _env_int("SUBJECT_Y_BASE_7TIME", 360)
            row_h = _env_int("SUBJECT_ROW_H_7TIME", 122)  # 8 rows including lunch
        else:
            right_x0 = _env_int("SUBJECT_X0_6TIME", _env_int("SUBJECT_X0", 365))
            right_x1 = _env_int("SUBJECT_X1_6TIME", _env_int("SUBJECT_X1", 990))
            y_base = _env_int("SUBJECT_Y_BASE_6TIME", 360)
            row_h = _env_int("SUBJECT_ROW_H_6TIME", 130)  # 7 rows including lunch

        for idx, r in enumerate(rows):
            cy0 = y_base + idx * row_h
            box_right = (right_x0, cy0 - 55, right_x1, cy0 + 55)

            label = r["label"]
            subj = r["subject"] or "수업 시간표"
            if len(subj) > 18:
                subj = subj[:17] + "…"
            if "점심" not in label:
                _draw_centered_text(d, box_right, subj, subj_font, fill="black")

    # Optional debug rectangles for calibration
    if (os.getenv("RENDER_DEBUG_BOXES", "false").lower() == "true"):
        # draw date box outline
        d.rectangle(date_box, outline="#ff0000", width=2)
        # draw a sample subject box outline (only if legacy box coords exist)
        if all(k in locals() for k in ("right_x0", "right_x1", "y_base")):
            d.rectangle((right_x0, y_base - 55, right_x1, y_base + 55), outline="#00aa00", width=2)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, quality=95)
    log.info("Saved image: %s (template=%s)", out_path, tpl_name)
    return out_path
