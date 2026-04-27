from Pronova.Utils.Logger import LOGGER

import os
import re
import asyncio
import aiohttp
import hashlib
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from .Models import Song as Track

DEFAULT_THUMB = "https://picsum.photos/1280/720"


# ---------- TEXT HELPERS ----------
def trim_to_width(text, font, max_w):
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text), 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis


def split_text(text):
    eng, hin = "", ""
    for ch in text:
        if ord(ch) < 128:
            eng += ch
        else:
            hin += ch
    return eng.strip(), hin.strip()


# ---------- MAIN CLASS ----------
class Thumbnail:
    def __init__(self):
        try:
            self.title_font = ImageFont.truetype("Cinzel-Black.ttf", 58)
            self.sub_font = ImageFont.truetype("Raleway-Bold.ttf", 30)
            self.meta_font = ImageFont.truetype("Inter-Light.ttf", 24)
            self.hindi_font = ImageFont.truetype("NotoSansDevanagari-Bold.ttf", 58)
        except:
            LOGGER.warning("Font load failed")
            self.title_font = self.sub_font = self.meta_font = self.hindi_font = ImageFont.load_default()

    # ---------- DOWNLOAD ----------
    async def save_thumb(self, path, url):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if not url:
            url = DEFAULT_THUMB

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    data = await r.read()
                    if not data or len(data) < 5000:
                        raise Exception("Bad image")

                    with open(path, "wb") as f:
                        f.write(data)

        except Exception as e:
            LOGGER.warning(f"Thumbnail download failed: {e}")

            async with aiohttp.ClientSession() as session:
                async with session.get(DEFAULT_THUMB) as r:
                    with open(path, "wb") as f:
                        f.write(await r.read())

        return path

    # ---------- GENERATE ----------
    async def generate(self, song: Track):
        try:
            sid = hashlib.md5((song.url or song.title).encode()).hexdigest()

            temp = f"cache/{sid}_temp.jpg"
            output = f"cache/{sid}.png"

            if os.path.exists(output) and os.path.getsize(output) > 10000:
                return output

            await self.save_thumb(temp, song.thumb)

            return await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync, temp, output, song
            )

        except Exception as e:
            LOGGER.error(f"Generate error: {e}")
            return DEFAULT_THUMB

    # ---------- IMAGE BUILDER ----------
    def _generate_sync(self, temp, output, song):
        try:
            base = Image.open(temp).resize((1280, 720)).convert("RGBA")

            # ===== BACKGROUND =====
            bg = ImageEnhance.Brightness(
                base.filter(ImageFilter.GaussianBlur(35))
            ).enhance(0.35)

            draw = ImageDraw.Draw(bg)

            # ===== TOP TAGS =====
            draw.rounded_rectangle((60, 60, 240, 110), 30, outline="white", width=2)
            draw.text((80, 75), "NOW PLAYING", fill="white", font=self.meta_font)

            draw.rounded_rectangle((1000, 60, 1220, 110), 30, outline="white", width=2)
            draw.text((1040, 75), "9XM Music", fill="white", font=self.meta_font)

            # ===== TITLE =====
            title = re.sub(r"\W+", " ", song.title).title()
            eng, hin = split_text(title)

            draw.text((80, 170),
                      trim_to_width(eng, self.title_font, 800),
                      fill="white", font=self.title_font)

            if hin:
                draw.text((80, 240),
                          trim_to_width(hin, self.hindi_font, 800),
                          fill="#ffcc66", font=self.hindi_font)

            # ===== META =====
            draw.text((80, 310), song.channel,
                      fill="#cccccc", font=self.sub_font)

            draw.text((80, 350),
                      f"{song.duration} • {song.views or '0 views'} • YouTube",
                      fill="#aaaaaa", font=self.meta_font)

            # ===== GLASS CARD =====
            card = Image.new("RGBA", (320, 420), (0, 0, 0, 160))
            mask = Image.new("L", card.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, 320, 420), 40, fill=255)
            bg.paste(card, (920, 150), mask)

            # ===== POSTER =====
            thumb = base.resize((260, 260))
            tmask = Image.new("L", thumb.size, 0)
            ImageDraw.Draw(tmask).rounded_rectangle((0, 0, 260, 260), 30, fill=255)
            bg.paste(thumb, (950, 170), tmask)

            # ===== MINI AVATAR =====
            avatar = thumb.resize((90, 90))
            amask = Image.new("L", avatar.size, 0)
            ImageDraw.Draw(amask).ellipse((0, 0, 90, 90), fill=255)
            bg.paste(avatar, (1130, 360), amask)

            # ===== PROGRESS BAR =====
            bar_x, bar_y = 80, 580
            bar_w = 1100

            draw.line((bar_x, bar_y, bar_x + bar_w, bar_y),
                      fill="#666", width=4)

            progress = int(bar_w * 0.4)

            # glow
            for i in range(6):
                draw.line((bar_x, bar_y, bar_x + progress, bar_y),
                          fill=(255, 140, 0, 40), width=6 + i)

            draw.line((bar_x, bar_y, bar_x + progress, bar_y),
                      fill="#ff8800", width=5)

            draw.ellipse(
                (bar_x + progress - 10, bar_y - 10,
                 bar_x + progress + 10, bar_y + 10),
                fill="#ffcc66"
            )

            # ===== WAVEFORM =====
            for i in range(85):
                x = bar_x + i * 13
                h = random.randint(6, 40)
                draw.line((x, bar_y - h, x, bar_y + h),
                          fill=(255, 180, 100), width=2)

            # ===== TIME =====
            draw.text((80, 610), "00:00",
                      fill="#cccccc", font=self.meta_font)

            end = "Live" if getattr(song, "is_live", False) else song.duration

            draw.text((1080, 610), end,
                      fill="#cccccc", font=self.meta_font)

            # ===== CONTROLS =====
            draw.text((540, 650), "⏮", fill="white", font=self.title_font)
            draw.text((610, 650), "⏸", fill="white", font=self.title_font)
            draw.text((680, 650), "⏭", fill="white", font=self.title_font)

            # ===== SAVE =====
            bg.save(output)

            try:
                os.remove(temp)
            except:
                pass

            return output

        except Exception as e:
            LOGGER.error(f"Sync error: {e}")
            return DEFAULT_THUMB
