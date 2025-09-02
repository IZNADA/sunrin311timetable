import os, datetime
from dotenv import load_dotenv
from fetch_neis import find_school_codes, get_timetable
from render_image import render_timetable_image
from detect_change import calc_hash, record_post
from utils import format_date_kr

load_dotenv()

def jst_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)

def run():
    SCHOOL_NAME = os.getenv("SCHOOL_NAME", "선린인터넷고등학교")
    SCHOOL_LEVEL = os.getenv("SCHOOL_LEVEL", "his")  # els/mis/his
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

    # Allow overriding target date via env (YYYYMMDD)
    target = os.getenv("TARGET_DATE_YYYYMMDD")
    if target and len(target) == 8 and target.isdigit():
        ymd = target
        try:
            dt = datetime.datetime.strptime(target, "%Y%m%d")
            date_str = format_date_kr(dt)
        except Exception:
            date_str = target[:4] + "-" + target[4:6] + "-" + target[6:8]
    else:
        ymd = jst_now().strftime("%Y%m%d")
        date_str = format_date_kr(jst_now())

    tt = get_timetable(SCHOOL_LEVEL, atpt, sd, ymd, GRADE, CLASS_NM, AY=AY, SEM=SEM)

    os.makedirs("out", exist_ok=True)
    out_path = f"out/{ymd}.jpg"
    render_timetable_image(
        date_str,
        tt,
        out_path,
        brand_color=BRAND,
        school_name=SCHOOL_NAME,
        grade=GRADE,
        class_nm=CLASS_NM,
    )

    h = calc_hash({"date": ymd, "timetable": tt})
    record_post(ymd, "local-neis", h)

    print(f"생성 완료: {out_path}")
    if not tt:
        print("※ 오늘 시간표가 비어 있습니다. (주말/방학/학기전환/반 번호 확인)")

if __name__ == "__main__":
    run()
