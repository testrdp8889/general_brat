"""
Kun davomida belgilangan vaqt oralig'larida guruhga tabiiy, hazilkash
xabar yozib, suhbatni "jonlantiradigan" bot.

Bitta workflow kuniga 4 marta (ertalab, peshin, tushlikdan keyin,
kechqurun) shu skriptni ishga tushiradi; skript o'zi qaysi vaqt
oralig'ida ekanini aniqlab, shunga mos uslubda xabar yaratadi.
"""

import requests
import time
import os
import random
from datetime import datetime, timezone, timedelta

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"

TASHKENT_OFFSET = timedelta(hours=5)


# Bot ba'zan shu odamlardan birini tanlab, unga ismi bilan do'stona hazil yozadi.
#   weight — qanchalik tez-tez tanlanishi (XAL ko'proq, shuning uchun 3)
#   hint   — shu odamga qanday uslubda hazil qilish haqida ko'rsatma
PEOPLE = {
    "XAL": {
        "weight": 3,
        "hint": (
            "Шути над XAL саркастично, по-дружески: тема шутки — будто он "
            "обещает сыграть, а потом «кидает» и не приходит. Позови его "
            "играть и слегка подколи. Примеры тона (не повторяй дословно, "
            "придумай своё): «XAL, сегодня играешь или опять обманешь?», "
            "«XAL, когда уже сыграем? Не бойся!»"
        ),
    },
    "Шероз": {
        "weight": 1,
        "hint": (
            "Мягко и по-дружески подтолкни Шероза: например, что без него "
            "катка не собирается, пусть собирает пацанов и зовёт играть. "
            "Не повторяй пример дословно, придумай своё."
        ),
    },
}
# Check-in xabarlarining qanchasi bironta odamga ismi bilan qaratiladi (0.5 = yarmi)
PERSONAL_MESSAGE_PROBABILITY = 0.5


def get_time_slot():
    """Hozirgi Toshkent vaqtiga qarab qaysi kun bo'lagi ekanini aniqlaydi."""
    tashkent_now = datetime.now(timezone.utc) + TASHKENT_OFFSET
    hour = tashkent_now.hour
    if 6 <= hour < 10:
        return "утро (люди только просыпаются и собираются на работу/по делам)"
    if 10 <= hour < 13:
        return "полдень (день в разгаре, люди могут быть заняты)"
    if 13 <= hour < 17:
        return "время после обеда (настроение немного падает, хочется отдохнуть)"
    return "вечер (день закончился, люди расслаблены, время лёгкого общения)"


def generate_message(slot):
    prompt = (
        "Ты — обычный живой участник Telegram-группы, а не бот: пишешь как "
        "настоящий друг. Группа называется «Генералы», там общаются геймеры "
        "про Command & Conquer Generals Zero Hour и мод Contra X.\n\n"
        f"Сейчас время суток: {slot}.\n\n"
        "Задача: напиши в группу 1-2 коротких предложения — естественно, "
        "с юмором, по-дружески (свободно, со сленгом), чтобы завязать или "
        "оживить разговор. Иногда задавай вопрос (кто во что играет, кто "
        "не спит), иногда просто шути или делись настроением, иногда "
        "связывай с Generals/Contra X — каждый раз по-разному, не повторяйся. "
        "Не обязательно начинать с приветствия, разнообразие важнее. "
        "Выведи только готовое сообщение, без вступлений и без кавычек."
    )
    if PEOPLE and random.random() < PERSONAL_MESSAGE_PROBABILITY:
        names = list(PEOPLE)
        target = random.choices(names, weights=[PEOPLE[n]["weight"] for n in names])[0]
        prompt += (
            f"\n\nВАЖНО: в этот раз обратись лично к участнику по имени "
            f"{target} и назови его по имени. "
            f"{PEOPLE[target]['hint']} "
            "Каждый раз придумывай новую фразу. Не оскорбляй и не пиши "
            "ничего, что реально обидит — только дружеская, лёгкая, "
            "саркастичная шутка, как между друзьями."
        )
    prompt += (
        "\n\nЯЗЫК: пиши СТРОГО по-русски, кириллицей. Не пиши по-узбекски "
        "и не используй латиницу (единственное исключение — ник XAL)."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    for model in GEMINI_MODELS:
        url = f"{GEMINI_BASE}{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(1, 3):
            try:
                response = requests.post(url, json=payload, timeout=40)
                if response.status_code == 404:
                    print(f"[{model}] mavjud emas (404), keyingisiga o'tamiz.")
                    break
                if not response.ok:
                    print(f"[{model}, {attempt}-urinish] {response.status_code} {response.text[:150]}")
                    response.raise_for_status()
                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    print(f"Muvaffaqiyatli: {model}")
                    return text
            except Exception as e:
                print(f"[{model}, {attempt}-urinish] Xato: {e}")
            if attempt < 2:
                time.sleep(8)
    return None


def send_to_telegram(text, max_retries=3):
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(TELEGRAM_URL, data=payload, timeout=10)
            response.raise_for_status()
            print("Xabar muvaffaqiyatli yuborildi.")
            return True
        except Exception as e:
            print(f"[{attempt}-urinish] Telegramga yuborishda xato: {e}")
            if attempt < max_retries:
                time.sleep(5)
    return False


def main():
    tashkent_hour = (datetime.now(timezone.utc) + TASHKENT_OFFSET).hour
    if tashkent_hour < 7 or tashkent_hour >= 22:
        print(f"Toshkent vaqti bilan soat {tashkent_hour}:00 — kechasi yozmaymiz. To'xtatildi.")
        return

    slot = get_time_slot()
    print(f"Vaqt bo'lagi: {slot}")

    message = generate_message(slot)
    if not message:
        print("Xabar yaratib bo'lmadi (Gemini ishlamadi). To'xtatildi.")
        return

    print(message)
    send_to_telegram(message)


if __name__ == "__main__":
    main()
