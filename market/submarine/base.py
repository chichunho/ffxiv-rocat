from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from submarine.enums import Status
from submarine.model import FollowupMessage, OperatorInfo, SailInfo, Submarine


class SubmarineLike(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def status(self) -> Status: ...

    @property
    def operator_info(self) -> OperatorInfo | None: ...

    @property
    def sail_info(self) -> SailInfo | None: ...

    @property
    def note(self) -> str: ...

    @property
    def followup_message(self) -> FollowupMessage | None: ...


class ManagedSubmarineBase(SubmarineLike, Protocol):
    @property
    def manager(self) -> SubmarineManagerBase: ...

    @property
    def submarine(self) -> Submarine: ...

    @property
    def internal_index(self) -> int: ...


class SubmarineManagerBase(Protocol):
    def dump(self): ...

    def upsert_timer(
        self,
        man_submarine: ManagedSubmarineBase,
        coros: list[Callable[[], Awaitable[None]]],
    ): ...

    def cancel_timer(
        self,
        man_submarine: ManagedSubmarineBase,
    ): ...
