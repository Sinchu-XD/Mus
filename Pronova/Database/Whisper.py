from Pronova.Database import db

whispers = db.whispers


async def save_whisper(wid, message, target, sender):
    try:
        await whispers.insert_one({
            "_id": wid,
            "msg": message,
            "target": target,
            "sender": sender
        })
    except:
        pass


async def get_whisper(wid):
    try:
        return await whispers.find_one({"_id": wid})
    except:
        return None
