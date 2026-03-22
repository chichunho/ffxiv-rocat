from collections.abc import Awaitable, Callable
from datetime import tzinfo

import discord

from dcview.submarine.infoboard import InfoBoardView
from submarine.config import ConfigManager
from submarine.manager import Manager
from worker.submarine import FollowupMessageWorkerGroup
from worker.worker import Worker


class InfoBoardDisplayer(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarine_manager: Manager,
        submarine_config: ConfigManager,
        sea_zh: dict[str, str],
        local_tz: tzinfo,
        permission_check: Callable[[discord.User | discord.Member], Awaitable[bool]],
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        self.interaction = interaction
        self.smgr = submarine_manager
        self.submarine_config = submarine_config
        self.sea_zh = sea_zh
        self.local_tz = local_tz
        self.view = None
        self.permission_check = permission_check
        self.fmsg_workers = fmsg_workers

    async def start(self):
        self.view = InfoBoardView(
            self.smgr,
            self.submarine_config,
            self.sea_zh,
            self.local_tz,
            self.permission_check,
            self.fmsg_workers,
        )
        await self.interaction.response.send_message(view=self.view)
        infoboard_msg = await self.interaction.original_response()
        self.view.set_message(infoboard_msg)

        self.submarine_config.infoboard_channel_id = infoboard_msg.channel.id
        self.submarine_config.infoboard_message_id = infoboard_msg.id
        self.submarine_config.dump()
