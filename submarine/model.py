from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple, Protocol

import discord

from submarine.enums import Sea, Status


@dataclass
class SailInfo:
    sea: Sea
    route: list[str]
    return_dt: datetime


@dataclass
class OperatorInfo:
    operator: discord.User | discord.Member
    editor: discord.User | discord.Member | None


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
    def followup_message_id(self) -> int | None: ...


@dataclass
class Submarine:
    name: str
    status: Status
    operator_info: OperatorInfo | None
    sail_info: SailInfo | None
    note: str
    followup_message_id: int | None


@dataclass
class ManagedSubmarine(SubmarineLike):
    instance: Submarine
    internal_index: int

    @property
    def name(self) -> str:
        return self.instance.name

    @property
    def status(self) -> Status:
        return self.instance.status

    @property
    def operator_info(self) -> OperatorInfo | None:
        return self.instance.operator_info

    @property
    def sail_info(self) -> SailInfo | None:
        return self.instance.sail_info

    @property
    def note(self) -> str:
        return self.instance.note

    @property
    def followup_message_id(self) -> int | None:
        return self.instance.followup_message_id


class SubmarineTuple(NamedTuple):
    name: str
    status: Status
    operator_info: OperatorInfo | None
    sail_info: SailInfo | None
    note: str
    followup_message_id: int
