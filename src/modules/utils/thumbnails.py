import asyncio
from io import BytesIO
import httpx
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from aiofiles.os import path as aiopath

from src.helpers import CachedTrack
from src.logger import LOGGER

FONTS = {
    "cfont": ImageFont.truetype("src/modules/utils/cfont.ttf", 15),
    "dfont": ImageFont.truetype("src/modules/utils/font2.otf", 12),
    "nfont": ImageFont.truetype("src/modules/utils/font.ttf", 10),
    "tfont": ImageFont.truetype("src/modules/utils/font.ttf", 20),
}


async def fetch_image(url: str) -> Image.Image | None:
    if not url:
        return None
    async with httpx.AsyncClient() as client:
        try:
            if url.startswith("https://is1-ssl.mzstatic.com"):
                url = url.replace("500x500bb.jpg", "600x600bb.jpg")
            response = await client.get(url, timeout=5)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGBA")

            if url.startswith("https://i.ytimg.com"):
                img = img.resize((640, 360), Image.Resampling.LANCZOS)
            elif url.startswith("http://c.saavncdn.com") or url.startswith("https://i1.sndcdn"):
                img = img.resize((640, 360), Image.Resampling.LANCZOS)

            return img
        except Exception as e:
            LOGGER.error("Image loading error: %s", e)
            return None


def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def draw_play_controls(draw: ImageDraw.Draw, position: tuple[int, int], duration: str):
    x, y = position
    circle_radius = 10  # Smaller play button
    center_x = x + circle_radius
    center_y = y + circle_radius

    # Draw smaller circular play button
    draw.ellipse(
        (x, y, x + 2 * circle_radius, y + 2 * circle_radius),
        fill=(255, 255, 255, 220)
    )

    # Smaller triangle play icon in center
    triangle = [
        (center_x - 4, center_y - 5),
        (center_x - 4, center_y + 5),
        (center_x + 5, center_y),
    ]
    draw.polygon(triangle, fill=(0, 0, 0, 255))

    # Text: 00:00 / duration
    duration_text = f"00:00 / {duration}"
    bbox = draw.textbbox((0, 0), duration_text, font=FONTS["dfont"])
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Draw text right next to triangle
    text_x = center_x + 20  # Less spacing
    text_y = center_y - text_height // 2
    draw.text((text_x, text_y), duration_text, font=FONTS["dfont"], fill=(220, 220, 220))


def make_sq(image: Image.Image, size: int = 125) -> Image.Image:
    width, height = image.size
    side = min(width, height)
    crop = image.crop((
        (width - side) // 2,
        (height - side) // 2,
        (width + side) // 2,
        (height + side) // 2
    ))
    resize = crop.resize((size, size), Image.Resampling.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=30, fill=255)

    rounded = ImageOps.fit(resize, (size, size))
    rounded.putalpha(mask)
    return rounded


async def gen_thumb(song: CachedTrack) -> str:
    save_dir = f"database/photos/{song.track_id}.png"
    if await aiopath.exists(save_dir):
        return save_dir

    try:
        title = song.name.strip()
        artist = (song.artist or "Spotify").strip()
        duration_sec = song.duration or 0

        original = await fetch_image(song.thumbnail)
        if not original:
            return ""

        # Fully blur the background
        blurred_bg = original.filter(ImageFilter.GaussianBlur(25)).convert("RGBA")
        draw = ImageDraw.Draw(blurred_bg)

        # Draw blurred darkened box
        content_box = (60, 60, 580, 300)
        dark_region = ImageEnhance.Brightness(blurred_bg.crop(content_box)).enhance(0.5)

        mask = Image.new("L", (content_box[2] - content_box[0], content_box[3] - content_box[1]), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, mask.size[0], mask.size[1]), 30, fill=255)
        blurred_bg.paste(dark_region, content_box, mask)

        # Album art (non-blurred)
        cover = make_sq(original)
        blurred_bg.paste(cover, (90, 110), cover)

        # Text and play controls
        draw = ImageDraw.Draw(blurred_bg)
        draw.text((230, 120), "Akshi Vibez", fill=(200, 200, 200), font=FONTS["nfont"])
        draw.text((230, 140), title[:30], fill=(255, 255, 255), font=FONTS["tfont"])
        draw.text((230, 175), artist[:30], fill=(255, 255, 255), font=FONTS["cfont"])
        draw_play_controls(draw, (230, 205), format_duration(duration_sec))

        await asyncio.to_thread(blurred_bg.save, save_dir)
        return save_dir if await aiopath.exists(save_dir) else ""

    except Exception as e:
        LOGGER.error(f"Thumbnail generation error: {e}")
        return ""
