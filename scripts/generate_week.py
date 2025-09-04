#!/usr/bin/env python
import os
import sys
import argparse
import datetime as dt
from pathlib import Path
from typing import List

from dotenv import load_dotenv
import pytz

# Ensure repo root is on sys.path to import `src` when invoked as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Reuse existing modules without modifying them
from src.fetch_neis import find_school_codes, get_timetable
from src.render_image import render_timetable_image


TZ = pytz.timezone("Asia/Seoul")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate timetable images for a date range (default: current week Mon–Fri)",
    )
    p.add_argument("--start", help="Start date YYYYMMDD (default: Monday of current week)")
    p.add_argument("--days", type=int, default=5, help="Number of days (default: 5)")
    p.add_argument("--include-weekend", action="store_true", help="Shortcut to 7 days from Monday")
    return p.parse_args()


def monday_of_week(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def format_date_kr(d: dt.date) -> str:
    weekdays = "월화수목금토일"
    # e.g., 2025년09월03일 수요일
    return f"{d.strftime('%Y년%m월%d일')} {weekdays[d.weekday()]}요일"


def date_list(start: dt.date, days: int) -> List[dt.date]:
    return [start + dt.timedelta(days=i) for i in range(days)]


def main():
    load_dotenv()

    args = parse_args()

    # Resolve date range
    if args.start:
        start = dt.datetime.strptime(args.start, "%Y%m%d").date()
    else:
        today = dt.datetime.now(TZ).date()
        start = monday_of_week(today)

    days = 7 if args.include_weekend else args.days

    # School/env settings (same defaults as daemon)
    school_name = os.getenv("SCHOOL_NAME", "선린인터넷고등학교")
    school_level = os.getenv("SCHOOL_LEVEL", "his")
    grade = int(os.getenv("GRADE", "3"))
    class_nm_env = os.getenv("CLASS_NM", "11")
    try:
        class_nm = int(class_nm_env)
    except Exception:
        class_nm = class_nm_env
    ay = os.getenv("AY") or None
    sem = os.getenv("SEM") or None
    brand = os.getenv("BRAND_COLOR_HEX", "#2A6CF0")

    # Find school codes once
    sc = find_school_codes(school_name)
    atpt, sd = sc["ATPT_OFCDC_SC_CODE"], sc["SD_SCHUL_CODE"]

    os.makedirs("out", exist_ok=True)

    for d in date_list(start, days):
        ymd = d.strftime("%Y%m%d")
        date_str = format_date_kr(d)
        tt = get_timetable(school_level, atpt, sd, ymd, grade, class_nm, AY=ay, SEM=sem)
        out_path = f"out/{ymd}.jpg"
        render_timetable_image(
            date_str,
            tt,
            out_path,
            brand_color=brand,
            school_name=school_name,
            grade=grade,
            class_nm=class_nm,
        )
        print(f"Generated: {out_path} ({len(tt)} periods)")


if __name__ == "__main__":
    main()
