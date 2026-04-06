import uuid
from pyrogram import Client, filters
from pyrogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from Pronova.Database import save_whisper, get_whisper
from Pronova.Bot import bos as app

@app.on_inline_query()
async def inline_handler(client, query):
    try:
        text = query.query.strip()

        if not text:
            return await query.answer(
                [],
                switch_pm_text="Type message + user",
                switch_pm_parameter="start"
            )

        parts = text.split()

        if len(parts) < 2:
            return await query.answer(
                [],
                switch_pm_text="Example: hello @user",
                switch_pm_parameter="help"
            )

        raw_target = parts[-1]
        message_text = " ".join(parts[:-1])

        if raw_target.startswith("@"):
            target = raw_target.lower()
            mention = raw_target
        else:
            target = raw_target
            mention = f"User (ID: {target})"

        wid = str(uuid.uuid4())

        # ✅ Save in Mongo
        await save_whisper(
            wid,
            message_text,
            target,
            query.from_user.id
        )

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("👀 Read Whisper", callback_data=f"w_{wid}")]]
        )

        result = InlineQueryResultArticle(
            title="Send Whisper",
            description=message_text,
            input_message_content=InputTextMessageContent(
                f"🤫 Whisper for {mention}\nTap to read"
            ),
            reply_markup=keyboard
        )

        await query.answer([result], cache_time=1)

    except Exception:
        try:
            await query.answer([], switch_pm_text="Error occurred", switch_pm_parameter="error")
        except:
            pass


@app.on_callback_query(filters.regex("^w_"))
async def callback_handler(client, query: CallbackQuery):
    try:
        wid = query.data.split("_")[1]
        user = query.from_user

        # ✅ Get from Mongo
        data = await get_whisper(wid)

        if not data:
            return await query.answer("Invalid whisper", show_alert=True)

        target = data["target"]
        sender_id = data["sender"]

        allowed = False

        # Sender allowed
        if user.id == sender_id:
            allowed = True

        # Receiver allowed
        if target.startswith("@"):
            if user.username and f"@{user.username.lower()}" == target:
                allowed = True
        else:
            if str(user.id) == target:
                allowed = True

        if not allowed:
            return await query.answer("Not for you", show_alert=True)

        # ✅ Show whisper
        await query.answer(f"💌 {data['msg']}", show_alert=True)

        # ✅ Edit message
        try:
            mention = user.mention

            new_text = f"✅ {mention} Read The Whisper\n\n🤫 Tap below to read again"

            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔁 Read Again", callback_data=f"w_{wid}")]]
            )

            await query.message.edit_text(
                new_text,
                reply_markup=keyboard
            )
        except:
            pass

    except Exception:
        try:
            await query.answer("Error", show_alert=True)
        except:
            pass


app.run()
