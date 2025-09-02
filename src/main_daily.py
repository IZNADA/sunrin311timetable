import os, datetime
from dotenv import load_dotenv
from fetch_neis import find_school_codes, get_timetable
from render_image import render_timetable_image
from detect_change import calc_hash, record_post
from post_instagram import upload_image_via_url
from utils import format_date_kr

load_dotenv()

def jst_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)

def build_caption(date_str, tt, school_name, grade, class_nm):
    lines = [f"[{school_name} {grade}학년 {class_nm}반 | {date_str}]"]
    if not tt:
        lines.append("오늘은 등록된 시간표가 없어요.")
    else:
        for i, row in enumerate(tt, start=1):
            subj = (row.get('subject', '-') or '-').strip()
            lines.append(f"{i}교시  {subj}")
    lines.append("\n※ 변경 시 '정정 게시물'을 올리고, 원본 캡션에 안내를 덧붙입니다.")
    lines.append("#학급공지 #시간표")
    return "\n".join(lines)

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

    sc = find_school_codes(SCHOOL_NAME)
    atpt, sd = sc["ATPT_OFCDC_SC_CODE"], sc["SD_SCHUL_CODE"]

    ymd = jst_now().strftime("%Y%m%d")
    date_str = format_date_kr(jst_now())
    tt = get_timetable(SCHOOL_LEVEL, atpt, sd, ymd, GRADE, CLASS_NM, AY=AY, SEM=SEM)

    os.makedirs("out", exist_ok=True)
    img_path = f"out/{ymd}.jpg"
    render_timetable_image(
        date_str,
        tt,
        img_path,
        brand_color=BRAND,
        school_name=SCHOOL_NAME,
        grade=GRADE,
        class_nm=CLASS_NM,
    )

    image_url = "https://example.com/placeholder.jpg"  # TEST_MODE에서는 실제 업로드 안 함
    caption = build_caption(date_str, tt, SCHOOL_NAME, GRADE, CLASS_NM)
    post_id = upload_image_via_url(image_url, caption)

    h = calc_hash({"date": ymd, "timetable": tt})
    record_post(ymd, str(post_id), h)
    print(f"[DAILY] 완료: post_id={post_id}, img={img_path}")

if __name__ == "__main__":
    run()
