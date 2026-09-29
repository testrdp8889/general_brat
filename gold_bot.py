import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from google import genai


# =========================
# API SOZLAMALARI
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOLD_API_KEY = os.getenv("GOLD_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GOLD_URL = "https://www.goldapi.io/api/XAU/USD"


# =========================
# OLTIN NARXINI OLISH
# =========================

def get_gold_data():

    headers = {
        "x-access-token": GOLD_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(
        GOLD_URL,
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        return None

    return response.json()


# =========================
# GEMINI AI TAHLILI
# =========================

def analyze_gold(gold_data):

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    price = gold_data.get("price")
    change = gold_data.get("ch")
    change_percent = gold_data.get("pcp")
    high = gold_data.get("high_price")
    low = gold_data.get("low_price")

    prompt = f"""
Sen oltin bozori bo'yicha AI tahlilchi yordamchisan.

XAU/USD ma'lumotlari:

Hozirgi narx: {price}
O'zgarish: {change}
O'zgarish foizi: {change_percent}%
Kunlik High: {high}
Kunlik Low: {low}

Shu ma'lumotlarni o'zbek tilida qisqa va tushunarli tahlil qil.

Quyidagilarni ko'rsat:

🪙 XAU/USD narxi
📈 Bozor yo'nalishi
🟢 Support
🔴 Resistance
📊 Bozor holati
🤖 AI xulosasi

Ma'lumot yetarli bo'lmasa, buni ayt.
Aniq foyda yoki zarar kafolatini bermagin.
Bu investitsiya maslahati emas.
"""

    result = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return result.text


# =========================
# /gold BUYRUG'I
# =========================

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⏳ Oltin bozori tekshirilmoqda..."
    )

    try:

        gold_data = get_gold_data()

        if not gold_data:
            await update.message.reply_text(
                "❌ Gold API'dan ma'lumot olinmadi."
            )
            return

        analysis = analyze_gold(gold_data)

        await update.message.reply_text(
            "🪙 GOLD — XAU/USD\n\n" + analysis
        )

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "❌ Xatolik yuz berdi. API sozlamalarini tekshiring."
        )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

def main():

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN topilmadi")
        return

    if not GOLD_API_KEY:
        print("❌ GOLD_API_KEY topilmadi")
        return

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY topilmadi")
        return

    app = Application.builder().token(
        TELEGRAM_TOKEN
    ).build()

    app.add_handler(
        CommandHandler("gold", gold)
    )

    print("🤖 GOLD AI BOT ISHLAYAPTI")

    app.run_polling()


if __name__ == "__main__":
    main()
