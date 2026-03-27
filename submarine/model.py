import asyncio
from dataclasses import dataclass
from datetime import datetime

import discord

from submarine.enums import Sea, Status
from worker.worker import Worker


@dataclass
class SailInfo:
    sea: Sea
    route: list[str]
    return_dt: datetime


@dataclass
class OperatorInfo:
    operator: discord.Member
    editor: discord.Member | None  # none if no one edit


@dataclass
class FollowupMessage:
    channel_id: int
    message_id: int


@dataclass
class Submarine:
    name: str
    status: Status
    operator_info: OperatorInfo | None  # none if idled
    sail_info: SailInfo | None  # none if idled
    note: str
    followup_message: FollowupMessage | None


@dataclass
class ExclusiveAsyncLock:
    lock: asyncio.Lock
    owner: discord.Member | None
    worker: Worker | None
    acquire_dt: datetime | None
