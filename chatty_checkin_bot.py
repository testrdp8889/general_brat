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
            "XAL ga kinoyali, do'stona hazillar yoz: hazil mavzusi — go'yo u "
            "o'yinga va'da berib, keyin 'aldab' qo'yadigandek; uni o'yinga "
            "chaqir va ozgina chimchilab qo'y. "
            "Ohang namunasi (aynan takrorlama, o'zing o'ylab top): "
            "'XAL bugun o'ynaysanmi yoki yana aldaysanmi!', "
            "'XAL qachon endi o'ynaymiz, qo'rqma!'"
        ),
    },
    "Шероз": {
        "weight": 1,
        "hint": (
            "Шероз ga yengil, do'stona turtki ber: masalan u yigitlarni "
            "yig'ib o'yinga chaqirmasa bo'lmayapti, sensiz katka yig'ilmayapti "
            "ruhida (aynan takrorlama, o'zing o'ylab top)."
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
    if PEOPLE and random.random() < PERSONAL_MESSAGE_PROBABILITY:
        names = list(PEOPLE)
        target = random.choices(names, weights=[PEOPLE[n]["weight"] for n in names])[0]
        prompt += (
            f"\n\nMUHIM: bu safar xabarni aynan {target} ismli odamga qarata "
            "yoz, uni ismi bilan chaqir. "
            f"{PEOPLE[target]['hint']} "
            "Har safar boshqacha, yangi gap o'ylab top. Haqorat qilma, "
            "chindan xafa qiladigan gap yozma — faqat do'stona, yengil, "
            "kinoyali hazil (o'rtoqlar orasidagi hazil kabi). RUS TILIDA yoz."
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
