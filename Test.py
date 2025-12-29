
import requests
import re
import time
import logging
import sys
import os
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import telebot
import Stats

# ================= НАСТРОЙКИ =================
CHECK_INTERVAL = 180
MAX_SENT_MATCHES = 1000
KZ_TZ = ZoneInfo("Asia/Almaty")
SENT_FILE = "sent_matches.txt"

# ================= TELEGRAM =================
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
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info("🚀 Скрипт запущен")

# ================= TELEGRAM =================
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ================= REQUESTS SESSION =================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "x-fsign": "SW9D1eZo"
})

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
logger.info(f"📦 Загружено матчей: {len(sent_matches)}")

# ================= FLASHSCORE =================
def get_live_matches():
    url = "https://46.flashscore.ninja/46/x/feed/f_1_0_5_ru-kz_1"

    try:
        r = session.get(url, timeout=15)
    except Exception as e:
        logger.warning(f"LIVE request error: {e}")
        return []

    if r.status_code != 200 or not r.text:
        logger.warning(f"LIVE bad response: {r.status_code}")
        return []

    blocks = re.split(r'¬~', r.text)
    live_matches = []
    current_league = ""

    for block in blocks:
        if block.startswith("ZA÷"):
            current_league = block.split("¬")[0][3:].strip()

        elif block.startswith("AA÷"):
            fields = {
                item.split("÷")[0]: item.split("÷")[1]
                for item in block.split("¬") if "÷" in item
            }

            if fields.get("AB") != "2" or fields.get("AI") != "y":
                continue

            if not (
                fields.get("AG") == "0" and
                fields.get("AH") == "0" and
                fields.get("AC") in ("38", "13")
            ):
                continue

            match_id = block.split("¬")[0].replace("AA÷", "")

            start_ts = int(fields.get("AD", 0))
            start_dt = (
                datetime.fromtimestamp(start_ts, tz=timezone.utc)
                .astimezone(KZ_TZ)
                .strftime("%d.%m.%y %H:%M")
                if start_ts else "Unknown"
            )

            live_matches.append({
                "id": match_id,
                "league": current_league,
                "home": fields.get("CX", "Unknown"),
                "away": fields.get("WN", "Unknown"),
                "score": "0-0",
                "start_time": start_dt
            })

    return live_matches

# ================= TELEGRAM =================
def send_to_telegram(match, stats):
    TSh, TSaw, SOTh, SOTaw, CONh, CONaw = stats

    text = (
        "✅ <b>ПОДХОДЯЩИЙ МАТЧ</b>\n"
        f"Лига: {match['league']}\n"
        f"{match['home']} vs {match['away']}\n"
        f"Счёт: {match['score']}\n\n"
        f"Удары: {TSh + TSaw}\n"
        f"В створ: {SOTh + SOTaw}\n"
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
        logger.error(f"MAIN error: {e}")
        time.sleep(CHECK_INTERVAL)
        continue

    for match in matches:
        if match["id"] in sent_matches:
            continue

        stats = Stats.parse_statistics(match["id"])
        if not stats:
            continue

        TSh, TSaw, SOTh, SOTaw, CONh, CONaw = stats

        if (TSh + TSaw) >= 11 and (SOTh + SOTaw) >= 4 and (CONh + CONaw) >= 3:
            send_to_telegram(match, stats)
            sent_matches.add(match["id"])
            save_sent_match(match["id"])

    # защита от утечки памяти
    if len(sent_matches) > MAX_SENT_MATCHES:
        sent_matches.clear()
        logger.warning("🧹 sent_matches очищен")

    time.sleep(CHECK_INTERVAL + random.randint(-30, 60))








