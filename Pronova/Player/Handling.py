from traceback import format_exc

from pytgcalls import filters
from pytgcalls.types import StreamEnded, ChatUpdate


def setup_handlers(core, plugin=None, on_end=None, on_vc_closed=None):

    @core.on_update(filters.stream_end())
    async def stream_end(_, update: StreamEnded):
        try:
        
            if on_end:
                await on_end(update.chat_id)

        except Exception:
            print(f"[on_end error]\n{format_exc()}")

    @core.on_update(
        filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT)
    )
    async def vc_closed(_, update: ChatUpdate):
        try:
    
            if on_vc_closed:
                await on_vc_closed(update.chat_id)

    
            if plugin:
                await plugin.on_vc_closed(update.chat_id)

        except Exception:
            print(f"[vc_closed error]\n{format_exc()}")
