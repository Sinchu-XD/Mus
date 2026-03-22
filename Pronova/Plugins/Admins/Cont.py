from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
import time

from Pronova.Bot import bot, engine
from Pronova.Utils.Font import sc
from Pronova.Database import is_auth
from Pronova.Database import is_banned, is_gbanned


ADMIN_CACHE = {}
LAST_ACTION = {}


def can_send(chat_id, cooldown=3):
    now = time.time()
    last = LAST_ACTION.get(chat_id, 0)
    if now - last < cooldown:
        return False
    LAST_ACTION[chat_id] = now
    return True


async def is_admin(chat_id, user_id):
    if not user_id:
        return False
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False


async def check_ban(m):
    if not m.from_user:
        return True

    uid = m.from_user.id
    chat_id = m.chat.id

    if await is_gbanned(uid):
        return True

    if await is_banned(chat_id, uid):
        return True

    return False


async def admin_only(m):
    if not m.from_user:
        return False

    uid = m.from_user.id
    chat_id = m.chat.id
    key = f"{chat_id}:{uid}"

    if key in ADMIN_CACHE:
        return ADMIN_CACHE[key]

    if await check_ban(m):
        ADMIN_CACHE[key] = False
        return False

    if await is_admin(chat_id, uid) or await is_auth(chat_id, uid):
        ADMIN_CACHE[key] = True
        return True

    ADMIN_CACHE[key] = False
    return False


async def safe_vc(action, *args):
    try:
        return await action(*args)
    except:
        return None


async def safe_reply(m, text):
    if can_send(m.chat.id):
        await m.reply(text, disable_notification=True)


@bot.on_message(filters.command("skip"))
async def skip(_, m):
    if not await admin_only(m):
        return
    await safe_vc(engine.vc.skip, m.chat.id)
    await safe_reply(m, sc("song skipped"))


@bot.on_message(filters.command(["stop", "end"]))
async def stop(_, m):
    if not await admin_only(m):
        return
    if m.chat.id in engine.vc.player.queues:
        await safe_vc(engine.vc.stop, m.chat.id)
    await safe_reply(m, sc("playback ended"))


@bot.on_message(filters.command("pause"))
async def pause(_, m):
    if not await admin_only(m):
        return
    await safe_vc(engine.vc.pause, m.chat.id)
    await safe_reply(m, sc("paused"))


@bot.on_message(filters.command("resume"))
async def resume(_, m):
    if not await admin_only(m):
        return
    await safe_vc(engine.vc.resume, m.chat.id)
    await safe_reply(m, sc("resumed"))


@bot.on_message(filters.command("previous"))
async def previous(_, m):
    if not await admin_only(m):
        return
    ok = await safe_vc(engine.vc.previous, m.chat.id)
    if ok:
        await safe_reply(m, sc("previous song"))
    else:
        await safe_reply(m, sc("no previous song"))


@bot.on_message(filters.command("seek"))
async def seek_cmd(_, m):
    if not await admin_only(m):
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
        await safe_reply(m, "Seek failed")


@bot.on_message(filters.command("queue"))
async def queue(_, m):
    if not await admin_only(m):
        return

    q = engine.vc.player.queues.get(m.chat.id)

    if not q or not getattr(q, "items", None):
        return await safe_reply(m, sc("queue empty"))

    text = sc("queue list") + "\n\n"

    for i, s in enumerate(q.items, 1):
        text += f"{i}. {s.title}\n"

    await safe_reply(m, text)
