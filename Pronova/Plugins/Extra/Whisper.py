import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Pronova.Bot import bot as app

WHISPERS = {}

@app.on_inline_query()
async def inline_handler(client, query):
    text = query.query.strip()

    if not text:
        return await query.answer(
            results=[],
            switch_pm_text="Type message + username/id",
            switch_pm_parameter="start"
        )

    parts = text.split()

    if len(parts) < 2:
        return await query.answer(
            results=[],
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

    whisper_id = str(uuid.uuid4())

    WHISPERS[whisper_id] = {
        "text": message_text,
        "target": target
    }

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("👀 Read Whisper", callback_data=f"w_{whisper_id}")]]
    )

    result = InlineQueryResultArticle(
        title="Send Whisper",
        description=message_text,
        input_message_content=InputTextMessageContent(
            f"🤫 Whisper for {mention}\n\nClick button to read"
        ),
        reply_markup=keyboard
    )

    await query.answer([result], cache_time=1)


@app.on_callback_query(filters.regex("^w_"))
async def callback_handler(client, query: CallbackQuery):
    whisper_id = query.data.split("_")[1]

    data = WHISPERS.get(whisper_id)

    if not data:
        return await query.answer("Expired or not found", show_alert=True)

    user = query.from_user
    target = data["target"]

    if target.startswith("@"):
        if not user.username:
            return await query.answer("You have no username", show_alert=True)

        if "@" + user.username.lower() != target:
            return await query.answer("Not for you", show_alert=True)

    else:
        if str(user.id) != target:
            return await query.answer("Not for you", show_alert=True)

    await query.answer(f"💌 {data['text']}", show_alert=True)


app.run()
