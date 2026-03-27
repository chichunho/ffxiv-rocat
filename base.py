import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

import discord
from discord.ext.commands.bot import BotBase

from utils.countdown_task import CountdownTaskWrapper


class CountdownTaskHandler(Protocol):
    def create_countdown(
        self,
        worker: CountdownTaskWrapper,
    ) -> asyncio.Task: ...


class AraguBotBase(BotBase, discord.Client, CountdownTaskHandler):
    async def upsert_scheduled_job(
        self,
        job_id: str,
        coro: Callable[[], Awaitable[None]],
    ) -> None: ...

    async def cancel_schedule_job(self, job_id: str) -> None: ...
