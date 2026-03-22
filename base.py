import asyncio
from typing import Protocol

import discord
from discord.ext.commands.bot import BotBase

from utils.countdown_task import CountdownTaskWrapper


class CountdownTaskHandler(Protocol):
    def create_countdown(
        self,
        worker: CountdownTaskWrapper,
    ) -> asyncio.Task: ...


class AraguBotBase(BotBase, discord.Client, CountdownTaskHandler): ...
