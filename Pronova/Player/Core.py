from pytgcalls import PyTgCalls


class EngineCore:
    def __init__(self, app):
        self.app = app
        self.core = PyTgCalls(app)

        # hooks
        self.on_end = None
        self.on_vc_closed = None

        # plugin (optional)
        self.plugin = None

    async def start(self):
        await self.core.start()
