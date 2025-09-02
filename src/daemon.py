import os
import datetime as dt
import argparse

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import get_logger, TZ
from .fetch_neis import find_school_codes, get_timetable
from .render_image import render_timetable_image
from .detect_change import calc_hash, record_post, last_hash
from .post_instagram import upload_image_via_url

log = get_logger(__name__)


def now_kr() -> dt.datetime:
    return dt.datetime.now(TZ)


def format_date_kr(d: dt.datetime) -> str:
    weekdays = "월화수목금토일"
    return d.strftime(f"%Y-%m-%d ({weekdays[d.weekday()]})")


def build_caption(date_str, tt, school_name, grade, class_nm):
    lines = [f"[{school_name} {grade}학년 {class_nm}반 | {date_str}]"]
    if not tt:
        lines.append("오늘은 등록된 시간표가 없어요.")
    else:
        for i, row in enumerate(tt, start=1):
            subj = (row.get('subject', '-') or '-').strip()
            lines.append(f"{i}교시  {subj}")
    lines.append("\n※ 자동 업로드 테스트 모드입니다.")
    lines.append("#학교계정 #시간표")
    return "\n".join(lines)


def daily_job():
    try:
        school_name = os.getenv("SCHOOL_NAME", "선린인터넷고등학교")
        school_level = os.getenv("SCHOOL_LEVEL", "his")
        grade = int(os.getenv("GRADE", "3"))
        class_nm = os.getenv("CLASS_NM", "11")
        try:
            class_nm = int(class_nm)
        except Exception:
            pass
        ay = os.getenv("AY") or None
        sem = os.getenv("SEM") or None
        brand = os.getenv("BRAND_COLOR_HEX", "#2A6CF0")

        sc = find_school_codes(school_name)
        atpt, sd = sc["ATPT_OFCDC_SC_CODE"], sc["SD_SCHUL_CODE"]

        ymd = now_kr().strftime("%Y%m%d")
        date_str = format_date_kr(now_kr())
        tt = get_timetable(school_level, atpt, sd, ymd, grade, class_nm, AY=ay, SEM=sem)

        os.makedirs("out", exist_ok=True)
        img_path = f"out/{ymd}.jpg"
        render_timetable_image(
            date_str,
            tt,
            img_path,
            brand_color=brand,
            school_name=school_name,
            grade=grade,
            class_nm=class_nm,
        )

        image_url = "https://example.com/placeholder.jpg"  # TEST mode: use external URL
        caption = build_caption(date_str, tt, school_name, grade, class_nm)

        previous_h = last_hash(ymd)
        current_h = calc_hash({"date": ymd, "timetable": tt})
        if previous_h and previous_h == current_h:
            log.info("No change detected for %s. Skipping post.", ymd)
            return

        post_id = upload_image_via_url(image_url, caption)
        record_post(ymd, str(post_id), current_h)
        log.info("Daily job done: post_id=%s, img=%s", post_id, img_path)
    except Exception as e:
        log.exception("Daily job failed: %s", e)


def main():
    parser = argparse.ArgumentParser(description="Insta timetable daemon")
    parser.add_argument("--run-now", action="store_true", help="Run the daily job once and exit")
    args = parser.parse_args()

    if args.run_now:
        log.info("Running daily job immediately (--run-now)")
        daily_job()
        return

    log.info("Starting scheduler (Asia/Seoul) with daily 07:00 job")
    scheduler = BackgroundScheduler(timezone=TZ)
    scheduler.add_job(daily_job, CronTrigger(hour=7, minute=0))
    scheduler.start()
    try:
        # Keep foreground alive
        while True:
            scheduler.print_jobs()
            # Sleep in long intervals
            import time
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()

