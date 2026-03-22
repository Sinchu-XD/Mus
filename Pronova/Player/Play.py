from pytgcalls.types import MediaStream, AudioQuality, VideoQuality


async def play(core, chat_id, stream, video=False):
    if not stream:
        raise Exception("Stream empty")

    if video:
        media = MediaStream(
            media_path=stream,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.HD_720p
        )
    else:
        media = MediaStream(
            media_path=stream,
            audio_parameters=AudioQuality.STUDIO,
            video_flags=MediaStream.Flags.IGNORE
        )

    await core.play(chat_id, media)
