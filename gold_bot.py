import requests
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =========================
# SOZLAMALAR
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("GOLD_API_KEY")

# Bu URL keyin sening Gold API'ingga moslanadi
API_URL = "https://www.goldapi.io/api/XAU/USD"


# =========================
# OLTIN NARXINI OLISH
# =========================

def get_gold_price():

    headers = {
        "x-access-token": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(API_URL, headers=headers)

    if response.status_code != 200:
        return None

    data = response.json()

    return data.get("price")


# =========================
# /gold BUYRUG'I
# =========================

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):

    price = get_gold_price()

    if price is None:
        await update.message.reply_text(
            "❌ Oltin narxini olishda xatolik yuz berdi."
        )
        return

    message = f"""
🪙 GOLD — XAU/USD

💰 Hozirgi narx:
${price}

📊 Tahlil:
Narx ma'lumotlari olindi.

🤖 AI tahlil modulini keyingi bosqichda qo'shamiz.

⚠️ Bu investitsiya tavsiyasi emas.
"""

    await update.message.reply_text(message)


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

def main():

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN topilmadi")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(
        CommandHandler("gold", gold)
    )

    print("🤖 Gold bot ishga tushdi...")

    app.run_polling()


if __name__ == "__main__":
    main()
