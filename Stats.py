import requests

headers = {
    "User-Agent": "Mozilla/5.0",
    "x-fsign": "SW9D1eZo"
}

stat_url = "https://46.flashscore.ninja/46/x/feed/df_st_1_{}"


def to_int(v):
    try:
        return int(v)
    except:
        return 0


def nz(x):
    return x if x is not None else 0


def parse_statistics(match_id):
    try:
        t = requests.get(
            stat_url.format(match_id),
            headers=headers,
            timeout=10
        ).text
    except Exception:
        # запрос не удался
        return None

    TSh = TSaw = None
    SOTh = SOTaw = None
    CONh = CONaw = None
    

    if "SE÷1-й тайм" in t:
        h1 = t.split("SE÷1-й тайм")[1].split("~SE÷")[0]

        for r in h1.split("~SD÷"):

            if "SG÷Всего ударов" in r:
                TSh = to_int(r.split("SH÷")[1].split("¬")[0])
                TSaw = to_int(r.split("SI÷")[1].split("¬")[0])

            if "SG÷Удары в створ" in r:
                SOTh = to_int(r.split("SH÷")[1].split("¬")[0])
                SOTaw = to_int(r.split("SI÷")[1].split("¬")[0])

            if "SG÷Угловые" in r:
                CONh = to_int(r.split("SH÷")[1].split("¬")[0])
                CONaw = to_int(r.split("SI÷")[1].split("¬")[0])
 

    stats = (
        nz(TSh), nz(TSaw),
        nz(SOTh), nz(SOTaw),
        nz(CONh), nz(CONaw),
    
    )

    # ❗ если статистики нет вообще — пропускаем матч
    if all(v == 0 for v in stats):
        return None

    return stats

