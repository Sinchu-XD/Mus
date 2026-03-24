import asyncio

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    UserAlreadyParticipant,
    PeerIdInvalid,
    UserBannedInChannel,
    UserNotParticipant,
    ChannelPrivate
)

from Pronova.Bot import bot, user
from Pronova.Utils.Font import sc


ASSISTANT_ID = None
ASSISTANT_USERNAME = None

JOINING = set()
LOCK = asyncio.Lock()


# -------------------- SETUP --------------------

async def setup_assistant():
    global ASSISTANT_ID, ASSISTANT_USERNAME

    async with LOCK:
        if ASSISTANT_ID:
            return

        me = await user.get_me()
        ASSISTANT_ID = me.id
        ASSISTANT_USERNAME = me.username or str(me.id)


# -------------------- CHECK --------------------

async def is_assistant_in_chat(chat_id):
    try:
        member = await user.get_chat_member(chat_id, ASSISTANT_ID)

        # Proper status check
        if member.status in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED
        ):
            return False

        return True

    except (UserNotParticipant, UserBannedInChannel, ChannelPrivate):
        return False

    except Exception as e:
        print(f"[Assistant Check Error] {e}")
        return False


# -------------------- MAIN --------------------

async def get_ass(chat_id, m=None):
    global ASSISTANT_ID

    if not ASSISTANT_ID:
        await setup_assistant()

    # Already in chat
    if await is_assistant_in_chat(chat_id):
        return True

    # Prevent duplicate joins
    if chat_id in JOINING:
        return False

    JOINING.add(chat_id)

    try:
        bot_me = await bot.get_me()
        bot_member = await bot.get_chat_member(chat_id, bot_me.id)

        # Bot must have invite permission
        if not bot_member.privileges or not bot_member.privileges.can_invite_users:
            raise ChatAdminRequired

        # Create invite link
        link = await bot.export_chat_invite_link(chat_id)

        try:
            await user.join_chat(link)
            await asyncio.sleep(2)

        except UserAlreadyParticipant:
            pass

        # Re-check after join
        joined = await is_assistant_in_chat(chat_id)

        if not joined:
            if m:
                await m.reply(sc("Assistant failed to join the chat."))
            return False

        return True


    # -------------------- BANNED HANDLING --------------------

    except UserBannedInChannel:
        try:
            bot_me = await bot.get_me()
            bot_member = await bot.get_chat_member(chat_id, bot_me.id)

            # Try auto-unban
            if bot_member.privileges and bot_member.privileges.can_restrict_members:
                await bot.unban_chat_member(chat_id, ASSISTANT_ID)
                await asyncio.sleep(1)

                try:
                    link = await bot.export_chat_invite_link(chat_id)
                    await user.join_chat(link)
                    await asyncio.sleep(2)

                    joined = await is_assistant_in_chat(chat_id)
                    if joined:
                        return True

                except Exception as e:
                    print(f"[Rejoin Error] {e}")

            if m:
                await m.reply(sc(
                    "Assistant is banned.\n"
                    "Please unban it manually."
                ))
            return False

        except Exception as e:
            print(f"[Auto Unban Error] {e}")

            if m:
                await m.reply(sc(
                    "Assistant is banned.\n"
                    "Please unban it manually."
                ))
            return False


    # -------------------- PERMISSION / ACCESS --------------------

    except (ChatAdminRequired, PeerIdInvalid):
        if m:
            await m.reply(
                sc(
                    "Assistant is not in the chat.\n"
                    "Give invite permission or add manually."
                )
                + f"\n\n@{ASSISTANT_USERNAME}\n`{ASSISTANT_ID}`"
            )
        return False


    except ChannelPrivate:
        if m:
            await m.reply(sc(
                "Assistant cannot access this chat.\n"
                "It may be banned or the chat is private."
            ))
        return False


    # -------------------- FALLBACK --------------------

    except Exception as e:
        print(f"[Assistant Join Error] {e}")
        if m:
            await m.reply(sc("Failed to bring assistant to the chat."))
        return False


    finally:
        JOINING.discard(chat_id)
