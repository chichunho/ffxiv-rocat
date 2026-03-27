import math
from datetime import datetime, timedelta

import pytz
from pytz import BaseTzInfo

from dcview.model import AwaredDatetime


def display_normalize(dt_str: str):
    _dt_substrs = dt_str.split()
    date_str, time_str = _dt_substrs[0], _dt_substrs[1]

    norm_dt_substrs: list[str] = []
    for idx, c in enumerate(date_str):
        # the first 5 char should be no problem
        # e.g. 2026/
        if idx < 5:
            norm_dt_substrs.append(c)
            continue

        # the shit game display 1 digit if possible in datetime, fix this by prefix 0 when needed
        # e.g.
        # 2026/3/
        #       ^dt_str[6]
        # 2026/10/
        #       ^dt_str[6]

        # check the next 2 char, if the latter char is a '/'
        # then prefix one 0 to the month digit
        if idx == 5 and dt_str[6] == "/":
            norm_dt_substrs.append("0")

        if idx == 7 and dt_str[6] == "/" and dt_str[8] == " ":
            norm_dt_substrs.append("0")

        if idx == 8 and dt_str[7] == "/" and dt_str[9] == " ":
            norm_dt_substrs.append("0")

        norm_dt_substrs.append(c)

    norm_dt_substrs.append(" ")
    if len(time_str) == 4:
        norm_dt_substrs.append("0")
    norm_dt_substrs.append(time_str)

    return "".join(norm_dt_substrs)


def timedelta2datetime(dt_str: str, local_tz: BaseTzInfo) -> AwaredDatetime | None:
    _ps = dt_str.split(",", maxsplit=2)

    if len(_ps) == 2:
        try:
            h, m = int(_ps[0].strip()), int(_ps[1].strip())
            if h > 60 or m > 60:
                return None
            return datetime.now(local_tz) + timedelta(hours=h, minutes=m)
        except (IndexError, ValueError):
            return None
    else:
        try:
            d, h, m = int(_ps[0].strip()), int(_ps[1].strip()), int(_ps[2].strip())
            if h > 60 or m > 60:
                return None
            return datetime.now(local_tz) + timedelta(days=d, hours=h, minutes=m)
        except (IndexError, ValueError):
            return None


def datetime2timedelta(local_datetime: AwaredDatetime) -> tuple[int, int, int]:
    _td = local_datetime - datetime.now(pytz.utc)
    _d = math.floor(_td / timedelta(days=1))
    _h = math.floor((_td - timedelta(days=_d)) / timedelta(hours=1))
    _m = math.floor(
        (_td - timedelta(days=_d) - timedelta(hours=_h)) / timedelta(minutes=1)
    )

    return (_d, _h, _m)
