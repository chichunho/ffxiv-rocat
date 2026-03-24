import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime

import discord
import pytz

from base import AraguBotBase
from submarine.model import ExclusiveAsyncLock, ManagedSubmarine, Submarine
from submarine.parser import Dumper
from utils.countdown_task import CountdownTaskWrapper
from worker.worker import CancellableWorker, Worker


class Manager:
    def __init__(self, submarines: list[Submarine], dumper: Dumper, bot: AraguBotBase):
        self.dumper = dumper
        self.bot = bot

        # for internal use
        self._unmanaged_submarines = submarines

        # for external access
        self.submarines: list[ManagedSubmarine] = [
            ManagedSubmarine(submarine, idx) for idx, submarine in enumerate(submarines)
        ]

        self.edit_locks: list[ExclusiveAsyncLock] = []
        self.timers: list[asyncio.Task | None] = []

        for _ in self.submarines:
            self.edit_locks.append(ExclusiveAsyncLock(asyncio.Lock(), None, None))
            self.timers.append(None)

    async def exclusive_update(
        self,
        interaction_user: discord.Member,
        submarine: ManagedSubmarine,
        worker: Worker,
    ) -> bool:
        # allow the same user to continue update same submarine
        if (
            self.edit_locks[submarine.internal_index].owner is not None
            and self.edit_locks[submarine.internal_index].owner != interaction_user
            and self.edit_locks[submarine.internal_index].lock.locked()
        ):
            return False
        else:
            try:
                lock_worker = self.edit_locks[submarine.internal_index].worker
                # if the worker can be cancelled, then cancel it
                if isinstance(lock_worker, CancellableWorker):
                    lock_worker.cancel()
                self.edit_locks[submarine.internal_index].lock.release()
            except RuntimeError:
                pass

        async with self.edit_locks[submarine.internal_index].lock:
            self.edit_locks[submarine.internal_index].owner = interaction_user
            self.edit_locks[submarine.internal_index].worker = worker
            await worker.start()
            self.dumper.dump(self._unmanaged_submarines)
            self.edit_locks[submarine.internal_index].owner = None
            self.edit_locks[submarine.internal_index].worker = None

        return True

    def dump(self):
        self.dumper.dump(self._unmanaged_submarines)

    def rename_all(self, names: list[str]):
        for idx, submarine in enumerate(self.submarines):
            submarine.instance.name = names[idx]
        self.dumper.dump(self._unmanaged_submarines)

    def is_locked(self, submarine: ManagedSubmarine):
        return self.edit_locks[submarine.internal_index].lock.locked()

    def upsert_timer(
        self,
        submarine: ManagedSubmarine,
        coros: list[Callable[[], Awaitable[None]]],
    ):
        timer = self.timers[submarine.internal_index]
        if timer is not None:
            timer.cancel()

        assert submarine.sail_info is not None
        countdown_seconds = max(
            (submarine.sail_info.return_dt - datetime.now(pytz.utc)).total_seconds(),
            0,
        )

        countdown_worker = CountdownTaskWrapper(int(countdown_seconds), coros)

        self.timers[submarine.internal_index] = self.bot.create_countdown(
            countdown_worker
        )

    def cancel_timer(self, submarine: ManagedSubmarine):
        timer = self.timers[submarine.internal_index]
        if timer is None:
            return

        timer.cancel()
        self.timers[submarine.internal_index] = None
