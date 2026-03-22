from pytgcalls.types import MediaStream, AudioQuality, VideoQuality


async def seek(core, chat_id, stream, start_time, video=False):
    if not stream:
        raise Exception("Stream empty")

    ffmpeg = f"-ss {start_time}" if start_time > 0 else None

    if video:
        media = MediaStream(
            media_path=stream,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.HD_720p,
            ffmpeg_parameters=ffmpeg
        )
    else:
        media = MediaStream(
            media_path=stream,
            audio_parameters=AudioQuality.STUDIO,
            video_flags=MediaStream.Flags.IGNORE,
            ffmpeg_parameters=ffmpeg
        )

    await core.play(chat_id, media)
