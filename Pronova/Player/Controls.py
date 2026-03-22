async def stop(core, chat_id):
    try:
        await core.leave_call(chat_id)
    except:
        pass


async def pause(core, chat_id):
    await core.pause(chat_id)


async def resume(core, chat_id):
    await core.resume(chat_id)


async def mute(core, chat_id):
    await core.mute(chat_id)


async def unmute(core, chat_id):
    await core.unmute(chat_id)
