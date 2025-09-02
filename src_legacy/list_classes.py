import os
from dotenv import load_dotenv
from fetch_neis import find_school_codes, list_classes
load_dotenv()
sc = find_school_codes(os.getenv("SCHOOL_NAME", "선린인터넷고등학교"))
rows = list_classes(sc["ATPT_OFCDC_SC_CODE"], sc["SD_SCHUL_CODE"], AY=os.getenv("AY") or None, GRADE=3)
print("학급 목록(3학년):")
for r in rows:
    if r.get("GRADE") == "3":
        print(f"- 반: {r.get('CLASS_NM')}  (학년도: {r.get('AY')})")
