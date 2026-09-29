"""
Kunlik oltin narxini Telegram guruhga yuboruvchi bot.

GitHub Actions versiyasi — hech qanday API kalit shart emas!
gold-api.com — to'liq bepul, ro'yxatdan o'tish talab qilmaydi.
Faqat Telegram token/chat ID GitHub Secrets'dan olinadi (ular allaqachon
Generals bot uchun qo'shilgan bo'lsa, qayta qo'shish shart emas).
"""

import requests
import time
import os
from datetime import datetime
from image_utils import create_card_image

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GOLD_API_URL = "https://api.gold-api.com/price/XAU"
EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/USD"
TELEGRAM_PHOTO_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

GRAMS_PER_OUNCE = 31.1035
FALLBACK_USD_TO_UZS = 12700  # kurs API ishlamay qolsa, shu zaxira qiymat ishlatiladi


def get_gold_price(max_retries=3):
    """gold-api.com'dan 1 untsiya oltin narxini USD'da oladi."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(GOLD_API_URL, timeout=10)
            response.raise_for_status()
            return response.json()["price"]
        except Exception as e:
            print(f"[{attempt}-urinish] Narx olishda xato: {e}")
            if attempt < max_retries:
                time.sleep(5)
    return None


def get_usd_to_uzs_rate(max_retries=3):
    """Jonli USD -> UZS kursini oladi. Ishlamasa, zaxira qiymatni qaytaradi."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(EXCHANGE_API_URL, timeout=10)
            response.raise_for_status()
            rate = response.json()["rates"]["UZS"]
            return rate
        except Exception as e:
            print(f"[{attempt}-urinish] Kursni olishda xato: {e}")
            if attempt < max_retries:
                time.sleep(5)
    print("Jonli kurs olinmadi, zaxira qiymat ishlatiladi.")
    return FALLBACK_USD_TO_UZS


def build_card_image(price_per_ounce_usd, usd_to_uzs):
    price_per_gram_usd = price_per_ounce_usd / GRAMS_PER_OUNCE
    price_per_gram_uzs = price_per_gram_usd * usd_to_uzs

    price_999 = price_per_gram_uzs
    price_585 = price_per_gram_uzs * 0.585

    today = datetime.now().strftime("%d.%m.%Y")

    body_text = (
        f"Проба 999: {price_999:,.0f} сум/г\n"
        f"Проба 585: {price_585:,.0f} сум/г\n\n"
        f"Унция: ${price_per_ounce_usd:,.2f}   •   Курс: {usd_to_uzs:,.0f} сум/$"
    )

    return create_card_image(
        title="Цена золота",
        subtitle=today,
        body_text=body_text,
        bg_color=(38, 30, 12),
        accent_color=(255, 205, 92),
    )


def send_photo_to_telegram(image_bytes, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            files = {"photo": ("gold.png", image_bytes, "image/png")}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            response = requests.post(
                TELEGRAM_PHOTO_URL, data=data, files=files, timeout=20
            )
            response.raise_for_status()
            print("Rasm muvaffaqiyatli yuborildi.")
            return True
        except Exception as e:
            print(f"[{attempt}-urinish] Telegramga yuborishda xato: {e}")
            if attempt < max_retries:
                time.sleep(5)
    return False


def main():
    price = get_gold_price()
    if price is None:
        print("Oltin narxini olib bo'lmadi. Dastur to'xtatildi.")
        return

    usd_to_uzs = get_usd_to_uzs_rate()

    image_bytes = build_card_image(price, usd_to_uzs)
    send_photo_to_telegram(image_bytes)


if __name__ == "__main__":
    main()
