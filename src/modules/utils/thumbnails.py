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


def resize_youtube_thumbnail(img: Image.Image) -> Image.Image:
    """
    Resize a YouTube thumbnail to 16:9 aspect ratio while keeping important content.
    
    Target resolution is 1280x720 (HD).
    """
    target_width = 1280
    target_height = 720
    aspect_ratio = img.width / img.height

    if aspect_ratio > (16/9):
        # Image is wider than 16:9
        new_width = int(target_height * aspect_ratio)
        new_height = target_height
    else:
        # Image is taller than 16:9
        new_width = target_width
        new_height = int(target_width / aspect_ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Crop to 1280x720 (center crop)
    left = (img.width - target_width) // 2
    top = (img.height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return img.crop((left, top, right, bottom))


def resize_jiosaavn_thumbnail(img: Image.Image) -> Image.Image:
    """
    Resize a JioSaavn thumbnail to 16:9 aspect ratio.
    
    Target resolution is 1280x720 (HD).
    """
    target_width = 1280
    target_height = 720
    
    # Resize the image to fill the target height
    new_width = int(target_height * (img.width / img.height))
    img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
    
    # If the resized image is wider than target_width, crop the sides
    if new_width > target_width:
        left = (new_width - target_width) // 2
        img = img.crop((left, 0, left + target_width, target_height))
    else:
        # If it's narrower, create a black background and center the image
        background = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 255))
        background.paste(img, ((target_width - new_width) // 2, 0), img.convert("RGBA"))
        img = background
        
    return img


async def fetch_image(url: str) -> Image.Image | None:
    """
    Fetches an image from the given URL, resizes it if necessary for JioSaavn and
    YouTube thumbnails, and returns the loaded image as a PIL Image object, or None on
    failure.

    Args:
        url (str): URL of the image to fetch.

    Returns:
        Image.Image | None: The fetched and possibly resized image, or None if the fetch fails.
    """
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
                img = resize_youtube_thumbnail(img)
            elif url.startswith("http://c.saavncdn.com") or url.startswith(
                "https://i1.sndcdn"
            ):
                img = resize_jiosaavn_thumbnail(img)
            return img
        except Exception as e:
            LOGGER.error("Image loading error: %s", e)
            return None


def clean_text(text: str, limit: int = 17) -> str:
    """
    Sanitizes and truncates text to fit within the limit.
    """
    text = text.strip()
    return f"{text[:limit - 3]}..." if len(text) > limit else text


def add_controls(img: Image.Image) -> Image.Image:
    """
    Adds blurred background effect and overlay controls.
    """
    img = img.filter(ImageFilter.GaussianBlur(25))
    box = (120, 120, 660, 440)

    region = img.crop(box)
    controls = Image.open("src/modules/utils/controls.png").convert("RGBA")
    dark_region = ImageEnhance.Brightness(region).enhance(0.5)

    mask = Image.new("L", dark_region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, box[2] - box[0], box[3] - box[1]), 40, fill=255
    )

    img.paste(dark_region, box, mask)
    img.paste(controls, (135, 305), controls)

    return img


def make_sq(image: Image.Image, size: int = 125) -> Image.Image:
    """
    Crops an image into a rounded square.
    """
    width, height = image.size
    side_length = min(width, height)
    crop = image.crop(
        (
            (width - side_length) // 2,
            (height - side_length) // 2,
            (width + side_length) // 2,
            (height + side_length) // 2,
        )
    )
    resize = crop.resize((size, size), Image.Resampling.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=30, fill=255)

    rounded = ImageOps.fit(resize, (size, size))
    rounded.putalpha(mask)
    return rounded


def get_duration(duration: int, time: str = "0:24") -> str:
    """
    Calculates remaining duration.
    """
    try:
        m1, s1 = divmod(duration, 60)
        m2, s2 = map(int, time.split(":"))
        sec = (m1 * 60 + s1) - (m2 * 60 + s2)
        _min, sec = divmod(sec, 60)
        return f"{_min}:{sec:02d}"
    except Exception as e:
        LOGGER.error("Duration calculation error: %s", e)
        return "0:00"


async def gen_thumb(song: CachedTrack) -> str:
    """
    Generates and saves a thumbnail for the song.
    """
    save_dir = f"database/photos/{song.track_id}.png"
    if await aiopath.exists(save_dir):
        return save_dir

    title, artist = clean_text(song.name), clean_text(song.artist or "Spotify")
    duration = song.duration or 0

    thumb = await fetch_image(song.thumbnail)
    if not thumb:
        return ""

    # Process Image
    bg = add_controls(thumb)
    image = make_sq(thumb)

    # Positions
    paste_x, paste_y = 155, 145
    bg.paste(image, (paste_x, paste_y), image)

    draw = ImageDraw.Draw(bg)
    draw.text((285, 180), "Yumi Music", (192, 192, 192), font=FONTS["nfont"])
    draw.text((285, 200), title, (255, 255, 255), font=FONTS["tfont"])
    draw.text((287, 235), artist, (255, 255, 255), font=FONTS["cfont"])
    draw.text((478, 321), get_duration(duration), (192, 192, 192), font=FONTS["dfont"])

    await asyncio.to_thread(bg.save, save_dir)
    return save_dir if await aiopath.exists(save_dir) else ""
