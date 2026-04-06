import uuid
from pyrogram import Client, filters
from Pronova.Bot import bot as app
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

WHISPERS = {}

@app.on_inline_query()
async def inline_whisper(client, query):
    text = query.query.strip()

    if not text:
        return await query.answer(
            results=[],
            switch_pm_text="Send a whisper",
            switch_pm_parameter="start"
        )

    parts = text.split()

    if len(parts) < 2:
        return await query.answer(
            results=[],
            switch_pm_text="Format: message @username or userid",
            switch_pm_parameter="help"
        )

    target = parts[-1]
    message_text = " ".join(parts[:-1])

    whisper_id = str(uuid.uuid4())

    WHISPERS[whisper_id] = {
        "text": message_text,
        "target": target.lower()
    }

    if target.startswith("@"):
        mention_text = target
    else:
        mention_text = f"User (ID: {target})"

    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("👀 Read Whisper", callback_data=f"whisper_{whisper_id}")]]
    )

    result = InlineQueryResultArticle(
        title="Send Whisper",
        description=message_text,
        input_message_content=InputTextMessageContent(
            f"🤫 Whisper for {mention_text}\n\nTap button to read the message"
        ),
        reply_markup=button
    )

    await query.answer([result], cache_time=1)

@app.on_callback_query(filters.regex("^whisper_"))
async def read_whisper(client, query: CallbackQuery):
    whisper_id = query.data.split("_")[1]

    data = WHISPERS.get(whisper_id)

    if not data:
        return await query.answer("Expired", show_alert=True)

    target = data["target"]
    user = query.from_user

    allowed = False

    if target.startswith("@"):
        if user.username and ("@" + user.username.lower() == target):
            allowed = True
    else:
        if str(user.id) == target:
            allowed = True

    if not allowed:
        return await query.answer("Not for you", show_alert=True)

    await query.answer(f"💌 {data['text']}", show_alert=True)

app.run()
