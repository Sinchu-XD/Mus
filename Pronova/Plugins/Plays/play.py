from pyrogram import filters
from pyrogram.types import Message

from Pronova.Player.Play import play
from Pronova.Utils.YouTube import resolve, get_valid_stream
from Pronova.Utils.Queue import queue
from Pronova.Utils.Queue import get_ass


async def play_next(core, chat_id):
    next_song = await queue.next(chat_id)

    if not next_song:
        return

    stream = await get_valid_stream(next_song)

    await play(core.core, chat_id, stream, video=False, plugin=core.plugin, song=next_song)
    queue.set_start(chat_id)


def register(app, core):
    core.on_end = lambda chat_id: play_next(core, chat_id)

    @app.on_message(filters.command("play") & filters.group)
    async def play_cmd(_, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if user:
            ok = await get_ass(chat_id, message)
            if not ok:
                return
    
        if message.reply_to_message and message.reply_to_message.audio:
            audio = message.reply_to_message.audio

            song = {
                "title": audio.title or "Telegram Audio",
                "duration": audio.duration,
                "duration_text": str(audio.duration),
                "url": None,
                "stream": audio.file_id,
                "thumb": None,
                "channel": "Telegram",
                "views": "Local",
                "is_video": False,
                "requested_by": {"id": user_id, "first_name": message.from_user.first_name}
            }

            pos = await queue.add(chat_id, song)

            if pos == 1:
                await play(core.core, chat_id, song["stream"], video=False, plugin=core.plugin, song=song)
                queue.set_start(chat_id)
            else:
                if core.plugin:
                    await core.plugin.on_queue_add(chat_id, song, pos)

            return

        query = message.text.split(None, 1)

        if len(query) < 2:
            return await message.reply_text("Give song name or URL")

        results = await resolve(query[1], video=False, user_id=user_id)

        if not results:
            return await message.reply_text("No results found")

        for song in results:
            pos = await queue.add(chat_id, song)

            if pos == 1:
                stream = await get_valid_stream(song)
                await play(core.core, chat_id, stream, video=False, plugin=core.plugin, song=song)
                queue.set_start(chat_id)
            else:
                if core.plugin:
                    await core.plugin.on_queue_add(chat_id, song, pos)
                    
