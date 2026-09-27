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
from datetime import datetime, timezone, timedelta

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
)

TASHKENT_OFFSET = timedelta(hours=5)


def get_time_slot():
    """Hozirgi Toshkent vaqtiga qarab qaysi kun bo'lagi ekanini aniqlaydi."""
    tashkent_now = datetime.now(timezone.utc) + TASHKENT_OFFSET
    hour = tashkent_now.hour
    if 6 <= hour < 10:
        return "ertalab (odamlar hali uyg'onib, ishga/kunga tayyorlanmoqda)"
    if 10 <= hour < 13:
        return "peshin (kun qizigan, odamlar band bo'lishi mumkin)"
    if 13 <= hour < 17:
        return "tushlikdan keyingi vaqt (kayfiyat biroz tushgan, dam kerak)"
    return "kechqurun (kun tugab, odamlar bo'shashgan, engilroq suhbat vaqti)"


def generate_message(slot):
    prompt = (
        "Sen Telegram guruhidagi oddiy, jonli ishtirokchisan — bot emas, "
        "haqiqiy do'st kabi yozasan. Guruh nomi 'Генералы', u yerda "
        "Command & Conquer Generals Zero Hour va uning Contra X modi "
        "haqida gaplashadigan gamer yigitlar bor.\n\n"
        f"Hozir kunning quyidagi bo'lagi: {slot}.\n\n"
        "Vazifa: guruhga 1-2 qisqa gapdan iborat, tabiiy, hazilkash, "
        "do'stona (erkin, sleng aralash) xabar yoz — bu suhbatni "
        "boshlab yuborish yoki jonlantirish uchun. RUS TILIDA yoz. "
        "Ba'zida savol ber (masalan kim nima o'ynayapti, kim uyg'oq "
        "kabi), ba'zida shunchaki hazil yoki kayfiyat ulashuvchi gap "
        "yoz, ba'zida Generals/Contra X mavzusiga bog'lab yubor — "
        "har safar har xil, takrorlanma. Salomlashish so'zi bilan "
        "HAR SAFAR boshlash shart emas, xilma-xillik muhim. "
        "Ortiqcha kirish so'zisiz, faqat tayyor xabarning o'zini yoz, "
        "tirnoqsiz."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    for attempt in range(1, 4):
        try:
            response = requests.post(GEMINI_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[{attempt}-urinish] Gemini xatosi: {e}")
            if attempt < 3:
                time.sleep(5)
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
