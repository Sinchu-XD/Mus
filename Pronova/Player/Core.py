from pytgcalls import PyTgCalls


class EngineCore:
    def __init__(self, app):
        self.app = app
        self.core = PyTgCalls(app)

    async def start(self):
        await self.core.start()
