import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime

import pytz

from base import AraguBotBase
from submarine.base import ManagedSubmarineBase, SubmarineManagerBase
from submarine.model import Submarine
from submarine.parser import Dumper
from submarine.submarine import ManagedSubmarine
from utils.countdown_task import CountdownTaskWrapper


class SubmarineManager(SubmarineManagerBase):
    def __init__(self, fp: str, bot: AraguBotBase, dumper: Dumper):
        self.fp = fp
        self.bot = bot
        self.dumper = dumper

        self._submarine: list[Submarine] = []
        self.timers: list[asyncio.Task | None] = []

    def manage(self, submarine: Submarine) -> ManagedSubmarine:
        self._submarine.append(submarine)
        man_sub = ManagedSubmarine(self, submarine, len(self._submarine))
        return man_sub

    def dump(self):
        self.dumper.dump(self._submarine)

    def upsert_timer(
        self,
        man_submarine: ManagedSubmarineBase,
        coros: list[Callable[[], Awaitable[None]]],
    ):
        timer = self.timers[man_submarine.internal_index]
        if timer is not None:
            timer.cancel()

        assert man_submarine.sail_info is not None
        countdown_seconds = max(
            (
                man_submarine.sail_info.return_dt - datetime.now(pytz.utc)
            ).total_seconds(),
            0,
        )

        countdown_worker = CountdownTaskWrapper(int(countdown_seconds), coros)

        self.timers[man_submarine.internal_index] = self.bot.create_countdown(
            countdown_worker
        )

    def cancel_timer(self, man_submarine: ManagedSubmarineBase):
        timer = self.timers[man_submarine.internal_index]
        if timer is None:
            return

        timer.cancel()
        self.timers[man_submarine.internal_index] = None
