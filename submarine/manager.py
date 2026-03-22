import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

import discord
import pytz

from base import AraguBotBase
from submarine.model import ManagedSubmarine, Submarine
from submarine.parser import Dumper
from utils.countdown_task import CountdownTaskWrapper
from worker.worker import Worker


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

        self.edit_locks: list[dict[str, Any]] = []
        self.timers: list[asyncio.Task | None] = []

        for _ in self.submarines:
            self.edit_locks.append(
                {
                    "lock": asyncio.Lock(),
                    "user": None,
                }
            )
            self.timers.append(None)

    async def exclusive_update(
        self,
        interaction_user: discord.User | discord.Member,
        submarine: ManagedSubmarine,
        worker: Worker,
    ) -> bool:
        # allow the same user to continue update same submarine
        if (
            self.edit_locks[submarine.internal_index]["user"] is not None
            and self.edit_locks[submarine.internal_index]["user"] != interaction_user
            and self.edit_locks[submarine.internal_index]["lock"].locked()
        ):
            return False
        else:
            lock = self.edit_locks[submarine.internal_index]["lock"]
            assert isinstance(lock, asyncio.Lock)
            try:
                lock.release()
            except RuntimeError:
                pass

        async with self.edit_locks[submarine.internal_index]["lock"]:
            self.edit_locks[submarine.internal_index]["user"] = interaction_user
            await worker.start()
            self.dumper.dump(self._unmanaged_submarines)
            self.edit_locks[submarine.internal_index]["user"] = None

        return True

    def dump(self):
        self.dumper.dump(self._unmanaged_submarines)

    def rename_all(self, names: list[str]):
        for idx, submarine in enumerate(self.submarines):
            submarine.instance.name = names[idx]
        self.dumper.dump(self._unmanaged_submarines)

    def is_locked(self, submarine: ManagedSubmarine):
        return self.edit_locks[submarine.internal_index]["lock"].locked()

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

        self.timers[submarine.internal_index] = self.bot.create_countdown(countdown_worker)

    def cancel_timer(self, submarine: ManagedSubmarine):
        timer = self.timers[submarine.internal_index]
        if timer is None:
            return

        timer.cancel()
        self.timers[submarine.internal_index] = None
