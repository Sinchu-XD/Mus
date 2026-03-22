from pytgcalls import PyTgCalls, filters
from pytgcalls.types import (
    MediaStream,
    AudioQuality,
    VideoQuality,
    StreamEnded,
    ChatUpdate
)


class _NativeEngine:
    def __init__(self, app):
        self._core = PyTgCalls(app)
        self.on_end = None
        self.on_vc_closed = None

        @self._core.on_update(filters.stream_end())
        async def _ended(_, update: StreamEnded):
            try:
                if self.on_end:
                    await self.on_end(update.chat_id)
            except Exception:
                pass

        @self._core.on_update(
            filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT)
        )
        async def _vc_closed(_, update: ChatUpdate):
            try:
                if self.on_vc_closed:
                    await self.on_vc_closed(update.chat_id)
            except Exception:
                pass

    async def start(self):
        await self._core.start()

    async def play(
        self,
        chat_id,
        stream,
        start_time: int = 0,
        video: bool = False
    ):
        if not stream:
            raise Exception("Stream empty")

        ffmpeg_params = None

        if isinstance(start_time, int) and start_time > 0:
            ffmpeg_params = f"-ss {start_time}"

        if video:
            media = MediaStream(
                media_path=stream,
                audio_parameters=AudioQuality.STUDIO,
                video_parameters=VideoQuality.HD_720p,
                ffmpeg_parameters=ffmpeg_params
            )
        else:
            media = MediaStream(
                media_path=stream,
                audio_parameters=AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters=ffmpeg_params
            )

        await self._core.play(chat_id, media)

    async def stop(self, chat_id):
        try:
            await self._core.leave_call(chat_id)
        except Exception:
            pass

    async def pause(self, chat_id):
        await self._core.pause(chat_id)

    async def resume(self, chat_id):
        await self._core.resume(chat_id)

    async def mute(self, chat_id):
        await self._core.mute(chat_id)

    async def unmute(self, chat_id):
        await self._core.unmute(chat_id)

    async def change_volume(self, chat_id, volume: int = 200):
        volume = max(0, min(volume, 200))
        await self._core.change_volume_call(chat_id, volume)
