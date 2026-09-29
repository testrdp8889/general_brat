import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from google import genai


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GOLD_URL = "https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT"


def get_gold_data():
    response = requests.get(
        GOLD_URL,
        timeout=10
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if not data.get("symbols"):
        return None

    return data["symbols"][0]


def analyze_gold(gold_data):
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    price = gold_data.get("price")
    computed_at = gold_data.get("computed_at")
    is_stale = gold_data.get("is_stale")

    prompt = f"""
Sen XAU/USD oltin bozori bo'yicha AI tahlilchi yordamchisan.

Hozirgi bozor ma'lumotlari:

XAU/USD narxi: {price} USD
Vaqt: {computed_at}
Ma'lumot eskirganmi: {is_stale}

Shu ma'lumot asosida o'zbek tilida qisqa va tushunarli tahlil qil.

Quyidagilarni ko'rsat:

🪙 XAU/USD narxi
📊 Bozor holati
📈 Yo'nalish bo'yicha kuzatuv
🟢 Muhim qo'llab-quvvatlash (agar aniqlash uchun ma'lumot yetarli bo'lsa)
🔴 Muhim qarshilik (agar aniqlash uchun ma'lumot yetarli bo'lsa)
🤖 AI xulosasi

MUHIM:
Faqat berilgan ma'lumotga asoslan.
Agar tarixiy narxlar yetarli bo'lmasa, aniq support/resistance,
RSI yoki boshqa texnik indikatorlarni o'ylab topma.
Ma'lumot yetarli emasligini ochiq ayt.

Aniq foyda yoki zarar kafolatini bermagin.
Bu investitsiya maslahati emas.
"""

    result = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return result.text


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


def main():

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN topilmadi")
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
