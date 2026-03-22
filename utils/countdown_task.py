import asyncio
from typing import Awaitable, Callable

from worker.worker import Worker


class CountdownTaskWrapper(Worker):
    def __init__(self, seconds: int, coros: list[Callable[[], Awaitable[None]]]):
        self.coros = coros
        self.seconds = seconds

    async def start(self):
        await asyncio.sleep(self.seconds)
        for coro in self.coros:
            await coro()
