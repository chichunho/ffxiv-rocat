from collections.abc import Awaitable, Callable

import discord
from pytz import BaseTzInfo

from dcview.submarine.infoboard import InfoBoardView
from submarine.config import ConfigManager
from submarine.seadict import SeaDict
from submarine.submarine import ManagedSubmarine
from utils.cache import DiscordGuildCache
from worker.submarine import FollowupMessageWorkerGroup
from worker.worker import Worker


class InfoBoardDisplayer(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarines: list[ManagedSubmarine],
        submarine_config: ConfigManager,
        sea_zh: SeaDict,
        local_tz: BaseTzInfo,
        permission_check: Callable[[discord.User | discord.Member], Awaitable[bool]],
        fmsg_workers: FollowupMessageWorkerGroup,
        guild_cache: DiscordGuildCache,
    ):
        self.interaction = interaction
        self.submarines = submarines
        self.submarine_config = submarine_config
        self.sea_zh = sea_zh
        self.local_tz = local_tz
        self.view = None
        self.permission_check = permission_check
        self.fmsg_workers = fmsg_workers
        self.guild_cache = guild_cache

    async def start(self):
        self.view = InfoBoardView(
            self.submarines,
            self.submarine_config,
            self.sea_zh,
            self.local_tz,
            self.permission_check,
            self.fmsg_workers,
            self.guild_cache,
        )
        await self.interaction.response.send_message(view=self.view)
        infoboard_msg = await self.interaction.original_response()
        self.view.set_message(infoboard_msg)

        self.submarine_config.infoboard_channel_id = infoboard_msg.channel.id
        self.submarine_config.infoboard_message_id = infoboard_msg.id
        self.submarine_config.dump()
