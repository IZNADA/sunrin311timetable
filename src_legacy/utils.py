import datetime as _dt

_WEEKDAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]


def weekday_kr(dt: _dt.datetime) -> str:
    try:
        return _WEEKDAYS_KR[dt.weekday()]
    except Exception:
        return ""


def format_date_kr(dt: _dt.datetime) -> str:
    ymd = dt.strftime("%Y-%m-%d")
    d = weekday_kr(dt)
    return f"{ymd} ({d})" if d else ymd

