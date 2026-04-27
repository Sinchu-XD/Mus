from Pronova.Utils.Logger import LOGGER

import os
import re
import asyncio
import aiohttp
import hashlib

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from .Models import Song as Track

DEFAULT_THUMB = "https://picsum.photos/1280/720"


# ---------- TEXT ----------
def trim(text, font, max_w):
    if font.getlength(text) <= max_w:
        return text
    while font.getlength(text + "...") > max_w:
        text = text[:-1]
    return text + "..."


# ---------- CLASS ----------
class Thumbnail:
    def __init__(self):
        try:
            self.title_font = ImageFont.truetype("Cinzel-Black.ttf", 56)
            self.sub_font = ImageFont.truetype("Raleway-Bold.ttf", 30)
            self.meta_font = ImageFont.truetype("Inter-Light.ttf", 24)
        except:
            self.title_font = self.sub_font = self.meta_font = ImageFont.load_default()

    async def save_thumb(self, path, url):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if not url:
            url = DEFAULT_THUMB

        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url) as r:
                    with open(path, "wb") as f:
                        f.write(await r.read())
        except:
            async with aiohttp.ClientSession() as s:
                async with s.get(DEFAULT_THUMB) as r:
                    with open(path, "wb") as f:
                        f.write(await r.read())

        return path

    async def generate(self, song: Track):
        sid = hashlib.md5((song.url or song.title).encode()).hexdigest()

        temp = f"cache/{sid}.jpg"
        out = f"cache/{sid}.png"

        if os.path.exists(out):
            return out

        await self.save_thumb(temp, song.thumb)

        return await asyncio.get_event_loop().run_in_executor(
            None, self._sync, temp, out, song
        )

    def _sync(self, temp, out, song):
        try:
            base = Image.open(temp).resize((1280, 720)).convert("RGBA")

            # ===== BG =====
            bg = base.filter(ImageFilter.GaussianBlur(28))
            bg = ImageEnhance.Brightness(bg).enhance(0.4)

            draw = ImageDraw.Draw(bg)

            # ===== TOP =====
            draw.rounded_rectangle((60, 60, 240, 110), 25, outline="white", width=2)
            draw.text((80, 75), "NOW PLAYING", fill="white", font=self.meta_font)

            draw.rounded_rectangle((1000, 60, 1220, 110), 25, outline="white", width=2)
            draw.text((1030, 75), "9XM Music", fill="white", font=self.meta_font)

            # ===== TITLE =====
            title = re.sub(r"\W+", " ", song.title).title()

            draw.text(
                (80, 170),
                trim(title, self.title_font, 800),
                fill="white",
                font=self.title_font
            )

            # ===== META =====
            draw.text((80, 260), song.channel,
                      fill="#cccccc", font=self.sub_font)

            draw.text((80, 300),
                      f"{song.duration} • {song.views or '0 views'} • YouTube",
                      fill="#aaaaaa", font=self.meta_font)

            # ===== RIGHT CARD =====
            card = Image.new("RGBA", (320, 420), (35, 35, 35, 210))
            mask = Image.new("L", (320, 420), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, 320, 420), 40, fill=255)
            bg.paste(card, (920, 150), mask)

            # ===== POSTER =====
            thumb = base.resize((260, 260))
            tmask = Image.new("L", (260, 260), 0)
            ImageDraw.Draw(tmask).rounded_rectangle((0, 0, 260, 260), 25, fill=255)
            bg.paste(thumb, (950, 170), tmask)

            # ===== AVATAR =====
            avatar = thumb.resize((80, 80))
            amask = Image.new("L", (80, 80), 0)
            ImageDraw.Draw(amask).ellipse((0, 0, 80, 80), fill=255)
            bg.paste(avatar, (1140, 360), amask)

            # ===== BAR =====
            bx, by = 80, 580
            bw = 1100

            draw.line((bx, by, bx + bw, by), fill="#555", width=4)

            progress = int(bw * 0.4)

            draw.line((bx, by, bx + progress, by),
                      fill="#ffaa33", width=6)

            draw.ellipse((bx + progress - 8, by - 8,
                          bx + progress + 8, by + 8),
                         fill="#ffcc66")

            # ===== WAVEFORM (CLEAN) =====
            for i in range(85):
                x = bx + i * 13
                h = 10 + (i % 10) * 3
                draw.line((x, by - h, x, by + h),
                          fill="#ffb366", width=2)

            # ===== TIME =====
            draw.text((80, 610), "00:00",
                      fill="#ccc", font=self.meta_font)

            draw.text((1080, 610), song.duration,
                      fill="#ccc", font=self.meta_font)

            # ===== CONTROLS =====
            draw.text((580, 650), "⏮", fill="white", font=self.sub_font)
            draw.text((640, 650), "⏸", fill="white", font=self.sub_font)
            draw.text((700, 650), "⏭", fill="white", font=self.sub_font)

            bg.save(out)

            try:
                os.remove(temp)
            except:
                pass

            return out

        except Exception as e:
            LOGGER.error(e)
            return DEFAULT_THUMB
