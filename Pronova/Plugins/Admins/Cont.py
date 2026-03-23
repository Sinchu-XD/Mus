from pyrogram import filters
import time

from Pronova.Bot import bot, engine
from Pronova.Utils.Font import sc
from Pronova.Utils.Allow import admin_only


LAST_ACTION = {}


def can_send(chat_id, cooldown=3):
    now = time.time()
    last = LAST_ACTION.get(chat_id, 0)
    if now - last < cooldown:
        return False
    LAST_ACTION[chat_id] = now
    return True


async def safe_vc(action, *args):
    try:
        return await action(*args)
    except:
        return None


async def safe_reply(m, text):
    if can_send(m.chat.id):
        try:
            await m.reply(text, disable_notification=True)
        except:
            pass


@bot.on_message(filters.command("skip") & filters.group)
async def skip(_, m):
    if not await admin_only(bot, message=m):
        return
    await safe_vc(engine.vc.skip, m.chat.id)
    await safe_reply(m, sc("song skipped"))


@bot.on_message(filters.command(["stop", "end"]) & filters.group)
async def stop(_, m):
    if not await admin_only(bot, message=m):
        return
    if m.chat.id in engine.vc.player.queues:
        await safe_vc(engine.vc.stop, m.chat.id)
    await safe_reply(m, sc("playback ended"))


@bot.on_message(filters.command("pause") & filters.group)
async def pause(_, m):
    if not await admin_only(bot, message=m):
        return
    await safe_vc(engine.vc.pause, m.chat.id)
    await safe_reply(m, sc("paused"))


@bot.on_message(filters.command("resume") & filters.group)
async def resume(_, m):
    if not await admin_only(bot, message=m):
        return
    await safe_vc(engine.vc.resume, m.chat.id)
    await safe_reply(m, sc("resumed"))


@bot.on_message(filters.command("previous") & filters.group)
async def previous(_, m):
    if not await admin_only(bot, message=m):
        return
    ok = await safe_vc(engine.vc.previous, m.chat.id)
    if ok:
        await safe_reply(m, sc("previous song"))
    else:
        await safe_reply(m, sc("no previous song"))


@bot.on_message(filters.command("seek") & filters.group)
async def seek_cmd(_, m):
    if not await admin_only(bot, message=m):
        return

    if len(m.command) < 2:
        return await safe_reply(m, "Usage: /seek 90 or 1:20")

    try:
        text = m.command[1]
        if ":" in text:
            parts = list(map(int, text.split(":")))
            seconds = sum(x * 60 ** i for i, x in enumerate(reversed(parts)))
        else:
            seconds = int(text)
    except:
        return await safe_reply(m, "Invalid format")

    ok = await safe_vc(engine.vc.seek, m.chat.id, seconds)
    if not ok:
        await safe_reply(m, sc("seek failed"))


@bot.on_message(filters.command("queue") & filters.group)
async def queue(_, m):
    if not await admin_only(bot, message=m):
        return

    q = engine.vc.player.queues.get(m.chat.id)

    if not q or not getattr(q, "items", None):
        return await safe_reply(m, sc("queue empty"))

    text = sc("queue list") + "\n\n"

    for i, s in enumerate(q.items, 1):
        title = getattr(s, "title", "Unknown")
        text += f"{i}. {title}\n"

    await safe_reply(m, text)
