from pyrogram.errors import (
    ChatAdminRequired,
    UserAlreadyParticipant,
    PeerIdInvalid,
    UserBannedInChannel
)

from Bot import bot, user
from Bot.Helper.Font import sc


ASSISTANT_ID = None
ASSISTANT_USERNAME = None

JOINING = set()


async def setup_assistant():
    global ASSISTANT_ID, ASSISTANT_USERNAME

    if ASSISTANT_ID:
        return

    me = await user.get_me()
    ASSISTANT_ID = me.id
    ASSISTANT_USERNAME = me.username or "NoUsername"

    print(f"Assistant Loaded → {ASSISTANT_ID}")


async def is_assistant_in_chat(chat_id):
    try:
        await bot.get_chat_member(chat_id, ASSISTANT_ID)
        return True
    except:
        return False


async def get_ass(chat_id, m):
    global ASSISTANT_ID

    if not ASSISTANT_ID:
        await setup_assistant()

    if await is_assistant_in_chat(chat_id):
        return True

    if chat_id in JOINING:
        return False

    JOINING.add(chat_id)

    try:
        bot_me = await bot.get_me()
        bot_member = await bot.get_chat_member(chat_id, bot_me.id)

        if not bot_member.privileges or not bot_member.privileges.can_invite_users:
            raise ChatAdminRequired

        link = await bot.export_chat_invite_link(chat_id)

        try:
            await user.join_chat(link)
        except UserAlreadyParticipant:
            return True

        if await is_assistant_in_chat(chat_id):
            return True

        return False

    except UserBannedInChannel:
        await m.reply(
            sc("assistant is banned in this group\nunban first")
        )
        return False

    except (ChatAdminRequired, PeerIdInvalid):
        await m.reply(
            sc(
                "assistant not in group\n"
                "give invite permission or add manually"
            )
            + f"\n\n@{ASSISTANT_USERNAME}\n`{ASSISTANT_ID}`"
        )
        return False

    except Exception as e:
        print("Assistant Join Error:", e)
        await m.reply(sc("failed to bring assistant"))
        return False

    finally:
        JOINING.discard(chat_id)
