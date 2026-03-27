from collections.abc import Awaitable, Callable

import discord
from pytz import BaseTzInfo

from base import AraguBotBase
from dcview.submarine.infoboard import AfterSubmarineReturn, InfoBoardView
from submarine.config import ConfigManager
from submarine.enums import Status
from submarine.manager import SubmarineManager
from submarine.parser import Loader as SubmarineLoader
from submarine.seadict import SeaDict
from utils.cache import DiscordGuildCache
from worker.submarine import FollowupMessageWorkerGroup
from worker.worker import Worker


class InfoBoardDisplayer(Worker):
    def __init__(
        self,
        bot: AraguBotBase,
        interaction: discord.Interaction,
        submarine_config: ConfigManager,
        submarine_manager: SubmarineManager,
        sea_zh: SeaDict,
        local_tz: BaseTzInfo,
        permission_check: Callable[[discord.User | discord.Member], Awaitable[bool]],
        fmsg_workers: FollowupMessageWorkerGroup,
        guild_cache: DiscordGuildCache | None = None,
    ):
        self.bot = bot
        self.interaction = interaction
        self.submarine_config = submarine_config
        self.submarine_manager = submarine_manager
        self.sea_zh = sea_zh
        self.local_tz = local_tz
        self.view = None
        self.permission_check = permission_check
        self.fmsg_workers = fmsg_workers
        self.guild_cache = guild_cache

    async def start(self):

        # check for if first call
        # if yes, init the config, cache, loader, and submarines
        if (
            self.submarine_config.infoboard_channel_id is None
            or self.submarine_config.infoboard_message_id is None
            or self.submarine_config.guild_id is None
        ):
            await self._init()

        # after init, or there is a exitsing board, all three of this will not be None
        assert self.fmsg_workers is not None
        assert self.guild_cache is not None

        # check if there is existing infoboard
        # if yes, respond with the link instead of creating a new infoboard
        infoboard_link = await self.get_infoboard_link()
        if infoboard_link is not None:
            await self.interaction.response.send_message(
                content=infoboard_link,
                ephemeral=True,
            )
            return

        # for the first call, or the board is not existed anymore
        # create a new board for the user

        self.view = InfoBoardView(
            self.submarine_manager,
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

        self.bot.add_view(self.view, message_id=infoboard_msg.id)
        await self.bot.upsert_scheduled_job(
            "submarine_regular_update", self.view.update
        )

    async def _init(self):
        # the interatcion must not come from DM
        assert self.interaction.channel is not None
        assert self.interaction.guild is not None

        self.submarine_config.guild_id = self.interaction.guild.id
        self.submarine_config.announce_channel_id = self.interaction.channel.id
        self.submarine_config.dump()

        self.guild_cache = DiscordGuildCache(
            await self.bot.fetch_guild(self.submarine_config.guild_id)
        )

        loader = SubmarineLoader(
            "submarine/data/state.json",
            self.guild_cache,
            self.local_tz,
        )

        submarines = []
        for submarine in await loader.load():
            submarines.append(self.submarine_manager.manage(submarine))

        self.fmsg_workers = FollowupMessageWorkerGroup(
            self.bot,
            self.submarine_config,
        )

    async def get_infoboard_link(self) -> str | None:

        if (
            self.submarine_config.infoboard_channel_id is None
            or self.submarine_config.infoboard_message_id is None
        ):
            return None

        try:
            infoboard_message = await discord.PartialMessage(
                channel=self.bot.get_partial_messageable(
                    self.submarine_config.infoboard_channel_id
                ),
                id=self.submarine_config.infoboard_message_id,
            ).fetch()
            return infoboard_message.jump_url
        except discord.NotFound:
            return None

    @staticmethod
    async def reconnect(
        bot: AraguBotBase,
        submarine_manager: SubmarineManager,
        submarine_config: ConfigManager,
        sea_zh: SeaDict,
        local_tz: BaseTzInfo,
        has_submarine_edit_permission: Callable[
            [discord.User | discord.Member], Awaitable[bool]
        ],
        submarine_followup_workers: FollowupMessageWorkerGroup,
        guild_cache: DiscordGuildCache | None,
    ):
        if (
            submarine_config.guild_id is None
            or submarine_config.infoboard_channel_id is None
            or submarine_config.infoboard_message_id is None
        ):
            return

        # since the submarine_config.guild_id is not None
        # the guild cacche obj will be created in the setup hook
        assert guild_cache is not None

        # try to get the infoboard if it exists
        try:
            infoboard_message = await discord.PartialMessage(
                channel=bot.get_partial_messageable(
                    submarine_config.infoboard_channel_id
                ),
                id=submarine_config.infoboard_message_id,
            ).fetch()
        except (discord.NotFound, discord.Forbidden):
            # reset the config
            submarine_config.infoboard_channel_id = None
            submarine_config.infoboard_message_id = None
            return

        # create an object to match the message
        infoboard = InfoBoardView(
            submarine_manager,
            submarine_config,
            sea_zh,
            local_tz,
            has_submarine_edit_permission,
            submarine_followup_workers,
            guild_cache,
        )

        infoboard.set_message(infoboard_message)
        bot.add_view(infoboard, message_id=infoboard_message.id)

        for submarine in submarine_manager.managed_submarines:
            if submarine.status is Status.SAIL:
                submarine.upsert_return_countdown(
                    AfterSubmarineReturn(
                        infoboard, submarine, submarine_followup_workers
                    ).callback
                )

        await infoboard.update()

        await bot.upsert_scheduled_job("submarine_regular_update", infoboard.update)
