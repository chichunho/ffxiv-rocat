import asyncio
from collections.abc import Awaitable, Callable

import discord

from submarine.base import (
    ManagedSubmarineBase,
    SubmarineManagerBase,
)
from submarine.enums import Status
from submarine.model import ExclusiveAsyncLock, OperatorInfo, SailInfo, Submarine
from worker.worker import CancellableWorker, Worker


class ManagedSubmarine(ManagedSubmarineBase):
    def __init__(
        self,
        manager: SubmarineManagerBase,
        submarine: Submarine,
        internal_index: int,
    ):
        self._manager = manager
        self._submarine = submarine
        self._internal_index = internal_index

        # exclusive update
        self.lock_state = ExclusiveAsyncLock(asyncio.Lock(), None, None)

    @property
    def manager(self) -> SubmarineManagerBase:
        return self._manager

    @property
    def submarine(self) -> Submarine:
        return self.submarine

    @property
    def internal_index(self) -> int:
        return self._internal_index

    def update(
        self,
        name: str | None = None,
        status: Status | None = None,
        operator_info: OperatorInfo | None = None,
        sail_info: SailInfo | None = None,
        note: str | None = None,
        followup_message_id: int | None = None,
    ):
        self.submarine.name = name or self.submarine.name
        self.submarine.status = status or self.submarine.status
        self.submarine.operator_info = operator_info or self.submarine.operator_info
        self.submarine.sail_info = sail_info or self.submarine.sail_info
        self.submarine.note = note or self.submarine.note
        self.submarine.followup_message_id = (
            followup_message_id or self.submarine.followup_message_id
        )

        self.manager.dump()

    async def exclusvice_update(
        self,
        owner: discord.Member,
        worker: Worker,
    ):
        if (
            self.lock_state.lock.locked()
            and self.lock_state.owner is not None
            and owner.id != self.lock_state.owner.id
        ):
            return False
        owned_worker = self.lock_state.worker
        if isinstance(owned_worker, CancellableWorker):
            owned_worker.cancel()
        try:
            self.lock_state.lock.release()
        except RuntimeError:
            return False

        async with self.lock_state.lock:
            self.lock_state.owner = owner
            self.lock_state.worker = worker

            await worker.start()
            self.manager.dump()

            self.lock_state.owner = None
            self.lock_state.worker = None

    def upsert_return_countdown(
        self,
        callbacks: list[Callable[[], Awaitable[None]]],
    ):
        self.manager.upsert_timer(self, callbacks)

    def cancel_return_countdown(self):
        self.manager.cancel_timer(self)
