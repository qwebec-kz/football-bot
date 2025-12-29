
import requests
import logging

logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "x-fsign": "SW9D1eZo"
})

STAT_URL = "https://46.flashscore.ninja/46/x/feed/df_st_1_{}"

def to_int(v):
    try:
        return int(v)
    except:
        return 0

def parse_statistics(match_id):
    try:
        r = session.get(STAT_URL.format(match_id), timeout=10)
    except Exception as e:
        logger.warning(f"STAT request error: {e}")
        return None

    if r.status_code != 200 or not r.text:
        return None

    t = r.text

    TSh = TSaw = SOTh = SOTaw = CONh = CONaw = 0

    if "SE÷1-й тайм" not in t:
        return None

    h1 = t.split("SE÷1-й тайм")[1].split("~SE÷")[0]

    for r in h1.split("~SD÷"):
        if "SG÷Всего ударов" in r:
            TSh = to_int(r.split("SH÷")[1].split("¬")[0])
            TSaw = to_int(r.split("SI÷")[1].split("¬")[0])

        elif "SG÷Удары в створ" in r:
            SOTh = to_int(r.split("SH÷")[1].split("¬")[0])
            SOTaw = to_int(r.split("SI÷")[1].split("¬")[0])

        elif "SG÷Угловые" in r:
            CONh = to_int(r.split("SH÷")[1].split("¬")[0])
            CONaw = to_int(r.split("SI÷")[1].split("¬")[0])

    if TSh + TSaw + SOTh + SOTaw + CONh + CONaw == 0:
        return None

    return TSh, TSaw, SOTh, SOTaw, CONh, CONaw
