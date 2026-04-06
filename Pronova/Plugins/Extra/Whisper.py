import uuid
from pyrogram import filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Pronova.Bot import bot as app
from Pronova.Utils.Logger import LOGGER

WHISPERS = {}

@app.on_inline_query()
async def inline_handler(client, query):
    try:
        text = query.query.strip()
        user = query.from_user

        LOGGER.info(f"INLINE_QUERY from {user.id} | query='{text}'")

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
            "target": target,
            "from": user.id
        }

        LOGGER.info(f"WHISPER_CREATED id={whisper_id} from={user.id} to={target} msg='{message_text}'")

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

    except Exception as e:
        LOGGER.error(f"INLINE_ERROR: {e}")


@app.on_callback_query(filters.regex("^w_"))
async def callback_handler(client, query: CallbackQuery):
    try:
        whisper_id = query.data.split("_")[1]
        user = query.from_user

        LOGGER.info(f"WHISPER_OPEN_ATTEMPT id={whisper_id} by={user.id}")

        data = WHISPERS.get(whisper_id)

        if not data:
            LOGGER.warning(f"WHISPER_EXPIRED id={whisper_id}")
            return await query.answer("Expired or not found", show_alert=True)

        target = data["target"]

        if target.startswith("@"):
            if not user.username:
                LOGGER.warning(f"NO_USERNAME user={user.id}")
                return await query.answer("You have no username", show_alert=True)

            if "@" + user.username.lower() != target:
                LOGGER.warning(f"UNAUTHORIZED_ACCESS id={whisper_id} by={user.id}")
                return await query.answer("Not for you", show_alert=True)

        else:
            if str(user.id) != target:
                LOGGER.warning(f"UNAUTHORIZED_ACCESS id={whisper_id} by={user.id}")
                return await query.answer("Not for you", show_alert=True)

        LOGGER.info(f"WHISPER_OPENED id={whisper_id} by={user.id}")

        await query.answer(f"💌 {data['text']}", show_alert=True)

    except Exception as e:
        LOGGER.error(f"CALLBACK_ERROR: {e}")
        await query.answer("Error occurred", show_alert=True)


app.run()
