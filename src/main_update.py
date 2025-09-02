import os, json, datetime
from dotenv import load_dotenv
from fetch_neis import find_school_codes, get_timetable
from render_image import render_timetable_image
from detect_change import calc_hash, record_post, STATE_PATH
from post_instagram import upload_image_via_url, edit_caption
from utils import format_date_kr

load_dotenv()

def jst_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)

def run():
    SCHOOL_NAME = os.getenv("SCHOOL_NAME", "선린인터넷고등학교")
    SCHOOL_LEVEL = os.getenv("SCHOOL_LEVEL", "his")
    GRADE = int(os.getenv("GRADE", "3"))
    CLASS_NM = os.getenv("CLASS_NM", "11")
    try:
        CLASS_NM = int(CLASS_NM)
    except Exception:
        pass
    AY  = os.getenv("AY") or None
    SEM = os.getenv("SEM") or None
    BRAND = os.getenv("BRAND_COLOR_HEX", "#2A6CF0")

    ymd = jst_now().strftime("%Y%m%d")

    state = {}
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass
    base = state.get(ymd)
    if not base:
        print("[UPDATE] 오늘 본 게시물이 없어 스킵합니다.")
        return

    sc = find_school_codes(SCHOOL_NAME)
    atpt, sd = sc["ATPT_OFCDC_SC_CODE"], sc["SD_SCHUL_CODE"]
    tt = get_timetable(SCHOOL_LEVEL, atpt, sd, ymd, GRADE, CLASS_NM, AY=AY, SEM=SEM)

    new_h = calc_hash({"date": ymd, "timetable": tt})
    if base.get("hash") == new_h:
        print("[UPDATE] 변경 없음.")
        return

    os.makedirs("out", exist_ok=True)
    date_str = format_date_kr(jst_now())
    upd_img = f"out/{ymd}_upd.jpg"
    render_timetable_image(
        date_str + " (업데이트)",
        tt,
        upd_img,
        brand_color=BRAND,
        school_name=SCHOOL_NAME,
        grade=GRADE,
        class_nm=CLASS_NM,
    )

    image_url = "https://example.com/placeholder_update.jpg"
    upd_caption = f"[정정] {SCHOOL_NAME} {GRADE}학년 {CLASS_NM}반 | {date_str}\n변경이 반영되었습니다."
    upd_id = upload_image_via_url(image_url, upd_caption)

    orig_id = base.get("post_id")
    try:
        edit_caption(orig_id, f"(정정 있음) 최신 게시물 ID: {upd_id}\n— 원본은 기록용으로 유지합니다.")
    except Exception as e:
        print("[WARN] 캡션 수정 실패:", e)

    record_post(ymd, orig_id, new_h)
    print(f"[UPDATE] 정정 완료: new_post_id={upd_id}, updated hash saved.")

if __name__ == "__main__":
    run()
