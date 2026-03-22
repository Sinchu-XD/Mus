from traceback import format_exc
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality


async def seek(
    core,
    chat_id,
    stream,
    start_time,
    video=False,
    plugin=None,
    song=None
):
    if not stream:
        raise Exception("Stream empty")

    if not isinstance(start_time, int):
        raise TypeError("start_time must be integer")

    ffmpeg = f"-ss {start_time}" if start_time > 0 else None

    try:
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

    
        if plugin and song:
            await plugin.on_seek(chat_id, song, start_time)

    except Exception:
        raise Exception(f"Seek failed:\n{format_exc()}")
