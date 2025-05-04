import random
import logging
import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch

logging.basicConfig(level=logging.INFO)

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage

def truncate(text):
    list = text.split(" ")
    text1 = ""
    text2 = ""    
    for i in list:
        if len(text1) + len(i) < 30:        
            text1 += " " + i
        elif len(text2) + len(i) < 30:       
            text2 += " " + i

    text1 = text1.strip()
    text2 = text2.strip()     
    return [text1,text2]

def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def generate_gradient(width, height, start_color, end_color):
    base = Image.new('RGBA', (width, height), start_color)
    top = Image.new('RGBA', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(60 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def add_border(image, border_width, border_color):
    width, height = image.size
    new_width = width + 2 * border_width
    new_height = height + 2 * border_width
    new_image = Image.new("RGBA", (new_width, new_height), border_color)
    new_image.paste(image, (border_width, border_width))
    return new_image

def crop_center_square(img, output_size, border, border_color):
    half_the_width = img.size[0] / 2
    half_the_height = img.size[1] / 2
    crop_size = output_size - 2 * border
    img = img.crop(
        (
            half_the_width - crop_size / 2,
            half_the_height - crop_size / 2,
            half_the_width + crop_size / 2,
            half_the_height + crop_size / 2,
        )
    )
    img = img.resize((output_size - 2 * border, output_size - 2 * border))
    final_img = Image.new("RGBA", (output_size, output_size), border_color)
    final_img.paste(img, (border, border))
    return final_img

def draw_text_with_shadow(background, draw, position, text, font, fill, shadow_offset=(3, 3), shadow_blur=5):
    
    shadow = Image.new('RGBA', background.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    
    shadow_draw.text(position, text, font=font, fill="black")
    
    
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    
    
    background.paste(shadow, shadow_offset, shadow)
    
    
    draw.text(position, text, font=font, fill=fill)

async def get_thumb(videoid: str):
    try:
        if os.path.isfile(f"cache/{videoid}_v4.png"):
            return f"cache/{videoid}_v4.png"

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            title = result.get("title", "Unsupported Title").title()
            duration = result.get("duration", "Live")
            thumbnail_url = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
            views = result.get("viewCount", {}).get("short", "Unknown Views")
            channel = result.get("channel", {}).get("name", "Unknown Channel")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                filepath = f"cache/thumb{videoid}.png"
                f = await aiofiles.open(filepath, mode="wb")
                await f.write(await resp.read())
                await f.close()

        image_path = f"cache/thumb{videoid}.png"
        youtube = Image.open(image_path)
        image1 = changeImageSize(1280, 720, youtube)

        background = image1.convert("RGBA").filter(ImageFilter.BoxBlur(20))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)

        start_color = random_color()
        end_color = random_color()
        gradient_image = generate_gradient(1280, 720, start_color, end_color)
        background = Image.blend(background, gradient_image, alpha=0.2)

        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype("src/assets/font2.ttf", 30)
        title_font = ImageFont.truetype("src/assets/font3.ttf", 45)

        square_thumbnail = crop_center_square(youtube, 400, 20, start_color)
        background.paste(square_thumbnail, (120, 160))
	

        text_x_position = 565
        title1 = truncate(title)
        draw_text_with_shadow(background, draw, (text_x_position, 180), title1[0], title_font, (255, 255, 255))
        draw_text_with_shadow(background, draw, (text_x_position, 230), title1[1], title_font, (255, 255, 255))
        draw_text_with_shadow(background, draw, (text_x_position, 320), f"{channel}  |  {views[:23]}", arial, (255, 255, 255))


        line_length = 580  
        line_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        if duration != "Live":
            color_line_percentage = random.uniform(0.15, 0.85)
            color_line_length = int(line_length * color_line_percentage)
            white_line_length = line_length - color_line_length

            start_point_color = (text_x_position, 380)
            end_point_color = (text_x_position + color_line_length, 380)
            draw.line([start_point_color, end_point_color], fill=line_color, width=9)
        
            start_point_white = (text_x_position + color_line_length, 380)
            end_point_white = (text_x_position + line_length, 380)
            draw.line([start_point_white, end_point_white], fill="white", width=8)
        
            circle_radius = 10 
            circle_position = (end_point_color[0], end_point_color[1])
            draw.ellipse([circle_position[0] - circle_radius, circle_position[1] - circle_radius,
                      circle_position[0] + circle_radius, circle_position[1] + circle_radius], fill=line_color)
    
        else:
            line_color = (255, 0, 0)
            start_point_color = (text_x_position, 380)
            end_point_color = (text_x_position + line_length, 380)
            draw.line([start_point_color, end_point_color], fill=line_color, width=9)
        
            circle_radius = 10 
            circle_position = (end_point_color[0], end_point_color[1])
            draw.ellipse([circle_position[0] - circle_radius, circle_position[1] - circle_radius,
                          circle_position[0] + circle_radius, circle_position[1] + circle_radius], fill=line_color)

        draw_text_with_shadow(background, draw, (text_x_position, 400), "00:00", arial, (255, 255, 255))
        draw_text_with_shadow(background, draw, (1080, 400), duration, arial, (255, 255, 255))
        
        play_icons = Image.open("src/assets/play_icons.png")
        play_icons = play_icons.resize((580, 62))
        background.paste(play_icons, (text_x_position, 450), play_icons)

        os.remove(f"cache/thumb{videoid}.png")

        background_path = f"cache/{videoid}_v4.png"
        background.save(background_path)
        
        return background_path

    except Exception as e:
        logging.error(f"Error generating thumbnail for video {videoid}: {e}")
        traceback.print_exc()
        return None
