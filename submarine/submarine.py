import asyncio
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from datetime import datetime, timedelta

import discord
import pytz

from submarine.base import ManagedSubmarineBase, SubmarineManagerBase
from submarine.enums import Status
from submarine.model import ExclusiveAsyncLock, FollowupMessage, OperatorInfo, SailInfo, Submarine
from worker.worker import CancellableWorker, Worker


class ManagedSubmarine(ManagedSubmarineBase):
    def __init__(
        self,
        manager: SubmarineManagerBase,
        submarine: Submarine,
        internal_index: int,
        lock_threshold: timedelta = timedelta(seconds=180),
    ):
        self._manager = manager
        self._submarine = submarine
        self._internal_index = internal_index
        self.lock_threshold = lock_threshold

        # exclusive update
        self.lock_state = ExclusiveAsyncLock(asyncio.Lock(), None, None, None)

    @property
    def manager(self) -> SubmarineManagerBase:
        return self._manager

    @property
    def submarine(self) -> Submarine:
        return self._submarine

    @property
    def internal_index(self) -> int:
        return self._internal_index

    @property
    def name(self) -> str:
        return self.submarine.name

    @property
    def status(self) -> Status:
        return self.submarine.status

    @property
    def operator_info(self) -> OperatorInfo | None:
        return self.submarine.operator_info

    @property
    def sail_info(self) -> SailInfo | None:
        return self.submarine.sail_info

    @property
    def note(self) -> str:
        return self.submarine.note

    @property
    def followup_message(self) -> FollowupMessage | None:
        return self.submarine.followup_message

    @contextmanager
    def update_ctx(self):
        yield self
        self.manager.dump()

    def replace(
        self,
        name: str | None = None,
        status: Status | None = None,
        operator_info: OperatorInfo | None = None,
        sail_info: SailInfo | None = None,
        note: str | None = None,
        followup_message: FollowupMessage | None = None,
    ):
        self.submarine.name = name or self.submarine.name
        self.submarine.status = status or self.submarine.status
        self.submarine.operator_info = operator_info or self.submarine.operator_info
        self.submarine.sail_info = sail_info or self.submarine.sail_info
        self.submarine.note = note or self.submarine.note
        self.submarine.followup_message = followup_message or self.submarine.followup_message

    def clear(
        self,
        operator_info: bool = False,
        sail_info: bool = False,
        note: bool = False,
        followup_message: bool = False,
    ):
        self.submarine.operator_info = None if operator_info else self.submarine.operator_info
        self.submarine.sail_info = None if sail_info else self.submarine.sail_info
        self.submarine.note = "" if note else self.submarine.note
        self.submarine.followup_message = (
            None if followup_message else self.submarine.followup_message
        )

    async def exclusive_update(
        self,
        owner: discord.Member,
        worker: Worker,
    ) -> bool:
        if self.lock_state.lock.locked():
            if (
                self.lock_state.owner is not None
                and owner.id != self.lock_state.owner.id
                and self.lock_state.acquire_dt is not None
                and (self.lock_state.acquire_dt - datetime.now(pytz.utc) < self.lock_threshold)
            ):
                return False

            # we are going to release the lock

            if self.lock_state.worker is not None and isinstance(
                self.lock_state.worker, CancellableWorker
            ):
                self.lock_state.worker.cancel()

            try:
                self.lock_state.lock.release()
            except RuntimeError:
                pass

        async with self.lock_state.lock:
            self.lock_state.owner = owner
            self.lock_state.worker = worker
            self.lock_state.acquire_dt = datetime.now(pytz.utc)

            await worker.start()

            self.lock_state.owner = None
            self.lock_state.worker = None
            self.lock_state.acquire_dt = None

        return True

    def upsert_return_countdown(
        self,
        callbacks: list[Callable[[], Awaitable[None]]],
    ):
        self.manager.upsert_timer(self, callbacks)

    def cancel_return_countdown(self):
        self.manager.cancel_timer(self)
