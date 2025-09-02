import json
import os
import re
from functools import lru_cache


@lru_cache(maxsize=1)
def _load_aliases():
    # 1) ENV inline JSON
    inline = os.getenv("SUBJECT_ALIASES")
    if inline:
        try:
            return json.loads(inline)
        except Exception:
            pass

    # 2) JSON file
    path = os.getenv("SUBJECT_ALIASES_PATH", "data/subject_aliases.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # 3) default: no aliases
    return {}


_LEADING_MARKS = tuple(["*", "•", "·", "-", "★", "※", "❖", "▶", "▷"])  # extend as needed


def _strip_leading_marks(s: str) -> str:
    # remove repeated leading marks + spaces
    i = 0
    while i < len(s) and (s[i] in _LEADING_MARKS or s[i].isspace()):
        i += 1
    return s[i:]


_space_re = re.compile(r"\s+")


def normalize_subject(name: str) -> str:
    if not name:
        return "-"
    s = str(name).strip()
    s = _strip_leading_marks(s)
    s = s.replace("\u00A0", " ")  # non-breaking spaces
    s = _space_re.sub(" ", s)
    # unify 2d/3d casing (common typo)
    s = re.sub(r"\b2d\b", "2D", s, flags=re.IGNORECASE)
    s = re.sub(r"\b3d\b", "3D", s, flags=re.IGNORECASE)

    # apply aliases after cleaning
    aliases = _load_aliases()
    try:
        repl = aliases.get(s)
        if isinstance(repl, str) and repl.strip():
            return repl.strip()
    except Exception:
        pass
    return s

