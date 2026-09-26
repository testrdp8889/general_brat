"""
GeneralsGameCode (TheSuperHackers) loyihasidagi yangi release/yangilikni
kuzatib, Telegram guruhga avtomatik yuboradigan bot.

GitHub Actions versiyasi — token va chat ID kodga yozilmaydi,
GitHub repository'ning "Secrets" bo'limidan avtomatik olinadi.
"""

import requests
import time
import os

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GITHUB_REPO = "TheSuperHackers/GeneralsGameCode"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
LAST_RELEASE_FILE = "last_release.txt"

MAX_CHANGELOG_LINES = 10


def translate_to_russian(text):
    """Bepul MyMemory API orqali inglizcha matnni ruschaga o'giradi.
    Agar tarjima ishlamasa, original (inglizcha) matnni qaytaradi."""
    if not text.strip():
        return text
    try:
        params = {"q": text, "langpair": "en|ru"}
        response = requests.get(
            "https://api.mymemory.translated.net/get", params=params, timeout=10
        )
        response.raise_for_status()
        data = response.json()
        translated = data.get("responseData", {}).get("translatedText")
        return translated if translated else text
    except Exception as e:
        print(f"Tarjima xatosi: {e}")
        return text


def get_latest_release(max_retries=3):
    headers = {"Accept": "application/vnd.github+json"}
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[{attempt}-urinish] GitHub'dan olishda xato: {e}")
            if attempt < max_retries:
                time.sleep(5)
    return None


def load_last_sent_tag():
    if os.path.exists(LAST_RELEASE_FILE):
        with open(LAST_RELEASE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def save_last_sent_tag(tag):
    with open(LAST_RELEASE_FILE, "w", encoding="utf-8") as f:
        f.write(tag)


def build_message(release):
    tag = release.get("tag_name", "неизвестно")
    url = release.get("html_url", "")
    body = release.get("body", "") or ""

    lines = [line for line in body.splitlines() if line.strip()]
    trimmed = lines[:MAX_CHANGELOG_LINES]

    translated_lines = []
    for line in trimmed:
        cleaned = line.lstrip("-* ").strip()
        translated_lines.append(translate_to_russian(cleaned))
        time.sleep(1)  # tarjima xizmatini haddan tashqari yuklamaslik uchun

    changelog_text = "\n".join(f"• {line}" for line in translated_lines)
    if len(lines) > MAX_CHANGELOG_LINES:
        changelog_text += f"\n… и еще {len(lines) - MAX_CHANGELOG_LINES} изменений"

    message = (
        f"🎮 *Generals Zero Hour — новое обновление!*\n\n"
        f"Версия: `{tag}`\n\n"
        f"{changelog_text if changelog_text else 'Подробности см. по ссылке.'}\n\n"
        f"🔗 {url}"
    )
    return message


def send_to_telegram(text, max_retries=3):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
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
    release = get_latest_release()
    if release is None:
        print("GitHub'dan ma'lumot olib bo'lmadi. Dastur to'xtatildi.")
        return

    tag = release.get("tag_name")
    last_sent = load_last_sent_tag()

    if tag == last_sent:
        print(f"Yangilik yo'q. Oxirgi yuborilgan: {tag}")
        return

    message = build_message(release)
    print(message)
    if send_to_telegram(message):
        save_last_sent_tag(tag)


if __name__ == "__main__":
    main()
