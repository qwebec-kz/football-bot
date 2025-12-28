import requests
import re
import time
import logging
import sys
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import telebot
import Stats

# ================= НАСТРОЙКИ =================
CHECK_INTERVAL = 5  # 3 минуты
KZ_TZ = ZoneInfo("Asia/Almaty")
SENT_FILE = "sent_matches.txt"

# ================= TELEGRAM (ENV) =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ НЕ ЗАДАНЫ TELEGRAM_TOKEN или CHAT_ID")
    sys.exit(1)

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d.%m.%y %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("🚀 Скрипт запущен")

# ================= TELEGRAM =================
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ================= SENT MATCHES =================
def load_sent_matches():
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def save_sent_match(match_id):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(match_id + "\n")


sent_matches = load_sent_matches()
logger.info(f"📦 Загружено отправленных матчей: {len(sent_matches)}")

# ================= FLASHSCORE =================
def get_live_matches():
    url = "https://46.flashscore.ninja/46/x/feed/f_1_0_5_ru-kz_1"
    headers = {"x-fsign": "SW9D1eZo"}

    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code != 200:
        return []

    blocks = re.split(r'¬~', response.text)

    live_matches = []
    current_league = ""

    for block in blocks:

        if block.startswith("ZA÷"):
            current_league = block.split("¬")[0][3:].strip()

        elif block.startswith("AA÷"):
            fields = {
                item.split("÷")[0]: item.split("÷")[1]
                for item in block.split("¬")
                if "÷" in item
            }

            match_id = block.split("¬")[0].replace("AA÷", "")

            if fields.get("AB") != "2" or fields.get("AI") != "y":
                continue

            home_score = fields.get("AG", "4")
            away_score = fields.get("AH", "0")

            if not (
                home_score == "4"
                and away_score == "0"
                and fields.get("AC") in ("38", "13")
            ):
                continue

            home = fields.get("CX", "Unknown")
            away = fields.get("WN", "Unknown") + " " + fields.get("AF", "")

            start_ts = int(fields.get("AD", 0))
            if start_ts:
                kz_time = datetime.fromtimestamp(
                    start_ts, tz=timezone.utc
                ).astimezone(KZ_TZ)
                start_dt = kz_time.strftime("%d.%m.%y %H:%M")
            else:
                start_dt = "Unknown"

            live_matches.append({
                "id": match_id,
                "league": current_league,
                "home": home,
                "away": away,
                "score": f"{home_score}-{away_score}",
                "start_time": start_dt
            })

    return live_matches


# ================= TELEGRAM =================
def send_to_telegram(match, stats):
    TSh, TSaw, SOTh, SOTaw, CONh, CONaw, YCh, YCaw = stats

    text = (
        "✅ <b>ПОДХОДЯЩИЙ МАТЧ</b>\n"
        f"Лига: {match['league']}\n"
        f"Матч: {match['home']} vs {match['away']}\n"
        f"Счёт: {match['score']}\n\n"
        f"Всего ударов: {TSh + TSaw}\n"
        f"Удары в створ: {SOTh + SOTaw}\n"
        f"Угловые: {CONh + CONaw}\n"
     
        f"Начало: {match['start_time']}"
    )

    bot.send_message(CHAT_ID, text, parse_mode="HTML")
    logger.info(f"📨 Отправлено: {match['home']} - {match['away']}")

# ================= ОСНОВНОЙ ЦИКЛ =================
logger.info("🔄 Мониторинг запущен")

while True:
    logger.info("⏰ Проверка")

    try:
        matches = get_live_matches()
    except Exception as e:
        logger.error(f"Ошибка LIVE: {e}")
        time.sleep(CHECK_INTERVAL)
        continue

    for match in matches:

        if match["id"] in sent_matches:
            continue

        stats = Stats.parse_statistics(match["id"])

        # ❗ НЕТ СТАТИСТИКИ — ПРОПУСКАЕМ
        if stats is None:
            logger.info(
                f"📭 Нет статистики: {match['home']} - {match['away']}"
            )
            continue

        TSh, TSaw, SOTh, SOTaw, CONh, CONaw  = stats

        if not (
            (TSh + TSaw) >= 3 and
            (SOTh + SOTaw) >= 3 and
            (CONh + CONaw) >= 3 and
        
        ):
            continue

        send_to_telegram(match, stats)
        sent_matches.add(match["id"])
        save_sent_match(match["id"])

    time.sleep(CHECK_INTERVAL)






