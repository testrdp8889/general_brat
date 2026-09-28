"""
Telegram uchun chiroyli "karta" ko'rinishidagi rasm yaratuvchi umumiy modul.
Ham oltin narxi boti, ham Generals yangiliklar boti shundan foydalanadi.
"""

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _wrap_line(draw, text, font, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _wrap_multiline(draw, text, font, max_width):
    all_lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            all_lines.append("")
            continue
        all_lines.extend(_wrap_line(draw, paragraph, font, max_width))
    return all_lines


def create_card_image(
    title,
    subtitle,
    body_text,
    bg_color=(22, 26, 36),
    accent_color=(255, 205, 92),
    text_color=(232, 234, 242),
    subtitle_color=(170, 176, 196),
    width=900,
):
    """Sarlavha + kichik matn + ko'p qatorli matndan iborat rasm (PNG bayt) yaratadi.
    Balandlik matn hajmiga qarab avtomatik moslashadi."""
    padding = 50
    title_font = ImageFont.truetype(FONT_BOLD_PATH, 44)
    subtitle_font = ImageFont.truetype(FONT_REGULAR_PATH, 24)
    body_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)

    temp_img = Image.new("RGB", (width, 100))
    temp_draw = ImageDraw.Draw(temp_img)

    max_text_width = width - padding * 2
    body_lines = _wrap_multiline(temp_draw, body_text, body_font, max_text_width)

    line_height = 42
    header_height = 150
    bottom_padding = 40
    height = header_height + len(body_lines) * line_height + bottom_padding

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, width, 8], fill=accent_color)

    y = 34
    draw.text((padding, y), title, font=title_font, fill=(255, 255, 255))
    y += 58
    draw.text((padding, y), subtitle, font=subtitle_font, fill=subtitle_color)
    y += 48

    for line in body_lines:
        draw.text((padding, y), line, font=body_font, fill=text_color)
        y += line_height

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
