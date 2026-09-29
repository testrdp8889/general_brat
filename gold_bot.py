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
Ты AI-аналитик рынка золота XAU/USD.

Текущие рыночные данные:

Цена XAU/USD: {price} USD
Время обновления: {computed_at}
Данные устарели: {is_stale}

Проведи краткий и понятный анализ на РУССКОМ языке.

Покажи:

🪙 Цена XAU/USD
📊 Состояние рынка
📈 Наблюдаемое направление движения
🟢 Важная поддержка — только если данных достаточно
🔴 Важное сопротивление — только если данных достаточно
🤖 Вывод AI

ВАЖНО:

Не выдумывай данные.

Если исторических данных недостаточно для определения поддержки,
сопротивления, RSI или других технических индикаторов,
прямо укажи, что данных недостаточно.

Не гарантируй прибыль или убыток.
Это не является инвестиционной рекомендацией.
"""

    result = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return result.text


async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⏳ Анализ рынка золота выполняется..."
    )

    try:
        gold_data = get_gold_data()

        if not gold_data:
            await update.message.reply_text(
                "❌ Не удалось получить данные о золоте."
            )
            return

        analysis = analyze_gold(gold_data)

        await update.message.reply_text(
            "🪙 GOLD — XAU/USD\n\n" + analysis
        )

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "❌ Произошла ошибка. Проверьте настройки API."
        )


def main():

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN не найден")
        return

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY не найден")
        return

    app = Application.builder().token(
        TELEGRAM_TOKEN
    ).build()

    app.add_handler(
        CommandHandler("gold", gold)
    )

    print("🤖 GOLD AI BOT ЗАПУЩЕН")

    app.run_polling()


if __name__ == "__main__":
    main()
