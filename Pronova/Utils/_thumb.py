from Pronova.Utils.Logger import LOGGER

import os
import re
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from .Models import Song as Track
import hashlib

DEFAULT_THUMB = "https://picsum.photos/1280/720"


# ---------- TEXT UTILS ----------
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
            self.title_font = ImageFont.truetype("Cinzel-Black.ttf", 60)
            self.sub_font = ImageFont.truetype("Raleway-Bold.ttf", 32)
            self.meta_font = ImageFont.truetype("Inter-Light.ttf", 26)
            self.hindi_font = ImageFont.truetype("NotoSansDevanagari-Bold.ttf", 60)
        except:
            LOGGER.warning("Font load failed, using default")
            self.title_font = self.sub_font = self.meta_font = self.hindi_font = ImageFont.load_default()

    # ---------- DOWNLOAD THUMB ----------
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
            LOGGER.warning(f"Thumb failed: {e}")

            async with aiohttp.ClientSession() as session:
                async with session.get(DEFAULT_THUMB) as r:
                    data = await r.read()
                    with open(path, "wb") as f:
                        f.write(data)

        return path

    # ---------- MAIN GENERATE ----------
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

    # ---------- IMAGE BUILD ----------
    def _generate_sync(self, temp, output, song):
        try:
            base = Image.open(temp).resize((1280, 720)).convert("RGBA")

            # 🎬 Cinematic blur background
            bg = ImageEnhance.Brightness(
                base.filter(ImageFilter.GaussianBlur(30))
            ).enhance(0.4)

            draw = ImageDraw.Draw(bg)

            # ===== TOP LABELS =====
            draw.rounded_rectangle((60, 50, 260, 110), 25, outline="white", width=2)
            draw.text((80, 70), "NOW PLAYING", fill="white", font=self.meta_font)

            draw.rounded_rectangle((1000, 50, 1220, 110), 25, outline="white", width=2)
            draw.text((1030, 70), "MUSIC", fill="white", font=self.meta_font)

            # ===== TITLE (ENG + HINDI FIX) =====
            title = re.sub(r"\W+", " ", song.title).title()
            eng, hin = split_text(title)

            draw.text((80, 180),
                      trim_to_width(eng, self.title_font, 800),
                      fill="white",
                      font=self.title_font)

            if hin:
                draw.text((80, 250),
                          trim_to_width(hin, self.hindi_font, 800),
                          fill="#ffcc66",
                          font=self.hindi_font)

            # ===== META =====
            draw.text((80, 320),
                      song.channel,
                      fill="#cccccc",
                      font=self.sub_font)

            draw.text((80, 360),
                      f"{song.duration} • {song.views or '0 views'} • YouTube",
                      fill="#aaaaaa",
                      font=self.meta_font)

            # ===== RIGHT IMAGE =====
            thumb = base.resize((260, 260))

            mask = Image.new("L", thumb.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, 260, 260), 30, fill=255)

            bg.paste(thumb, (950, 180), mask)

            # ===== PROGRESS BAR =====
            bar_x, bar_y = 80, 580
            bar_w = 1100

            draw.line((bar_x, bar_y, bar_x + bar_w, bar_y),
                      fill="#444", width=6)

            progress = int(bar_w * 0.4)

            draw.line((bar_x, bar_y, bar_x + progress, bar_y),
                      fill="#ff8800", width=6)

            draw.ellipse(
                (bar_x + progress - 10, bar_y - 10,
                 bar_x + progress + 10, bar_y + 10),
                fill="white"
            )

            draw.text((80, 600), "00:00",
                      fill="#aaaaaa", font=self.meta_font)

            end = "Live" if getattr(song, "is_live", False) else song.duration

            draw.text((1080, 600), end,
                      fill="#aaaaaa", font=self.meta_font)

            # ===== CONTROLS =====
            draw.text((540, 640), "⏮", fill="white", font=self.title_font)
            draw.text((610, 640), "⏸", fill="white", font=self.title_font)
            draw.text((680, 640), "⏭", fill="white", font=self.title_font)

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
