"""
GeneralsGameCode (TheSuperHackers) loyihasidagi yangi release/yangilikni
kuzatib, Telegram guruhga avtomatik yuboradigan bot.

GitHub Actions versiyasi — token va chat ID kodga yozilmaydi,
GitHub repository'ning "Secrets" bo'limidan avtomatik olinadi.
"""

import requests
import time
import os
from image_utils import create_card_image

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GITHUB_REPO = "TheSuperHackers/GeneralsGameCode"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
TELEGRAM_PHOTO_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
)
LAST_RELEASE_FILE = "last_release.txt"

MAX_CHANGELOG_LINES = 25  # AI'ga yuboriladigan xom qatorlar soni (chiqishda qisqaradi)


def analyze_for_contra_x(changelog_raw, tag):
    """Gemini AI orqali changelog'ni tahlil qiladi: ruschaga o'giradi va
    Contra X mod uchun aynan nimasi foydali ekanini ajratib ko'rsatadi.
    Ishlamasa — None qaytaradi (chaqiruvchi funksiya zaxira usulga o'tadi)."""
    prompt = (
        "Sen Command & Conquer Generals Zero Hour o'yinining ochiq manba "
        "engine loyihasi (GeneralsGameCode)dagi yangi release changelog'ini "
        "tahlil qilyapsan. Quyida o'sha changelog matni (inglizcha, GitHub'dan):\n\n"
        f"{changelog_raw}\n\n"
        "Vazifa: shu o'zgarishlarni o'qib, ular ichidan 'Contra X' nomli "
        "mashhur community mod (bu ham xuddi shu engine'ga asoslangan, INI "
        "fayllar, generals/general obyektlari, weapon/upgrade/particle "
        "tizimlari orqali ishlaydi) uchun FOYDALI yoki AHAMIYATLI bo'lgan "
        "narsalarni ajratib chiqar. Masalan: modding API'lari, -mod orqali "
        "yuklash imkoniyatlari, INI parser o'zgarishlari, bug fix'lar (agar "
        "mod ham shu bugdan aziyat chekishi mumkin bo'lsa), yangi engine "
        "imkoniyatlari, limitlarni oshirish (masalan max unit, max effect), "
        "yoki performance/crash tuzatishlari.\n\n"
        "Javobni RUS tilida, quyidagi formatda yoz:\n"
        "Qisqa umumiy xulosa (1-2 gap) qanday holatida ekanini, keyin "
        "'⚙️ Полезно для Contra X:' sarlavhasi ostida 2-5 ta bullet "
        "(agar chindan ham modding uchun ahamiyatli narsa bo'lsa — har "
        "birini 1 qatorda, nega foydali ekanini ham qisqa tushuntir). "
        "Agar hech narsa modding uchun ahamiyatli bo'lmasa, aynan shuni "
        "yoz: 'Bu safar Contra X uchun alohida ahamiyatli o'zgarish yo'q.' "
        "Ortiqcha kirish so'zlarsiz, to'g'ridan-to'g'ri javob ber."
    )

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    for attempt in range(1, 4):
        try:
            response = requests.post(GEMINI_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[{attempt}-urinish] Gemini tahlilida xato: {e}")
            if attempt < 3:
                time.sleep(5)
    return None


def fallback_translate(text):
    """Gemini ishlamay qolsa ishlatiladigan zaxira tarjima (MyMemory, bepul)."""
    if not text.strip():
        return text
    try:
        params = {"q": text[:490], "langpair": "en|ru"}
        response = requests.get(
            "https://api.mymemory.translated.net/get", params=params, timeout=10
        )
        response.raise_for_status()
        translated = response.json().get("responseData", {}).get("translatedText")
        return translated if translated else text
    except Exception as e:
        print(f"Zaxira tarjima xatosi: {e}")
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


def build_card_and_caption(release):
    tag = release.get("tag_name", "неизвестно")
    url = release.get("html_url", "")
    body = release.get("body", "") or ""

    lines = [line.lstrip("-* ").strip() for line in body.splitlines() if line.strip()]
    trimmed = lines[:MAX_CHANGELOG_LINES]
    changelog_raw = "\n".join(trimmed)

    analysis = analyze_for_contra_x(changelog_raw, tag) if changelog_raw else None

    if analysis:
        body_text = analysis
    else:
        # Zaxira: AI ishlamasa, oddiy qator-baqator tarjima qilamiz
        print("AI tahlili ishlamadi, zaxira tarjimaga o'tildi.")
        translated_lines = [fallback_translate(line) for line in trimmed[:10]]
        body_text = "\n".join(f"• {line}" for line in translated_lines)
        if not body_text:
            body_text = "Подробности см. по ссылке."

    image_bytes = create_card_image(
        title="🎮 Generals Zero Hour",
        subtitle=f"Обновление: {tag}",
        body_text=body_text,
        bg_color=(18, 28, 22),
        accent_color=(120, 200, 140),
    )
    caption = f"🔗 {url}"
    return image_bytes, caption


def send_photo_to_telegram(image_bytes, caption, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            files = {"photo": ("update.png", image_bytes, "image/png")}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
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
    release = get_latest_release()
    if release is None:
        print("GitHub'dan ma'lumot olib bo'lmadi. Dastur to'xtatildi.")
        return

    tag = release.get("tag_name")
    last_sent = load_last_sent_tag()

    if tag == last_sent:
        print(f"Yangilik yo'q. Oxirgi yuborilgan: {tag}")
        return

    image_bytes, caption = build_card_and_caption(release)
    if send_photo_to_telegram(image_bytes, caption):
        save_last_sent_tag(tag)


if __name__ == "__main__":
    main()
