from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
import time

from Pronova.Bot import bot, engine
from Pronova.Utils.Font import sc
from Pronova.Database import is_banned, is_gbanned


LAST_ACTION = {}


def can_send(chat_id, cooldown=3):
    now = time.time()
    last = LAST_ACTION.get(chat_id, 0)

    if now - last < cooldown:
        return False

    LAST_ACTION[chat_id] = now
    return True


async def safe_action(action, chat_id):
    try:
        return await action(chat_id)
    except:
        return None


async def is_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False


async def safe_reply(m, text):
    if can_send(m.chat.id):
        await m.reply(text, disable_notification=True)


@bot.on_callback_query(filters.regex("^vc_"))
async def vc_buttons(_, cq):

    await cq.answer()

    if not cq.message:
        return

    m = cq.message
    chat_id = m.chat.id
    user = cq.from_user

    if not user or user.is_bot:
        return

    uid = user.id

    if await is_gbanned(uid):
        return await cq.answer(sc("you are gbanned"), show_alert=True)

    if await is_banned(chat_id, uid):
        return await cq.answer(sc("you are banned in this chat"), show_alert=True)

    if not await is_admin(chat_id, uid):
        return await cq.answer(sc("only admins"), show_alert=True)

    if cq.data == "vc_skip":
        await safe_action(engine.vc.skip, chat_id)
        await safe_reply(m, sc("song skipped"))

    elif cq.data == "vc_end":
        if chat_id in engine.vc.player.queues:
            await safe_action(engine.vc.stop, chat_id)
        await safe_reply(m, sc("playback ended"))

    elif cq.data == "vc_pause":
        await safe_action(engine.vc.pause, chat_id)
        await safe_reply(m, sc("paused"))

    elif cq.data == "vc_resume":
        await safe_action(engine.vc.resume, chat_id)
        await safe_reply(m, sc("resumed"))
