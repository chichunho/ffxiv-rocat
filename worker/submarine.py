from collections.abc import Callable
from datetime import tzinfo

import discord

from base import AraguBotBase
from dcview.submarine.config import ConfigModal
from dcview.submarine.modal import SailEditModal, SailStartModal
from dcview.submarine.rename import RenameModal
from submarine.config import ConfigManager
from submarine.enums import Sea, Status
from submarine.manager import Manager
from submarine.model import ManagedSubmarine, OperatorInfo, SailInfo
from worker.worker import Worker


class SailStarter(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarine: ManagedSubmarine,
        smgr: Manager,
        cfg: ConfigManager,
        sea_zh: dict[str, str],
        local_tz: tzinfo,
        after_countdown: list[Callable],
    ):
        self.interaction = interaction
        self.submarine = submarine
        self.smgr = smgr
        self.cfg = cfg
        self.sea_zh = sea_zh
        self.local_tz = local_tz
        self.after_countdown = after_countdown
        self.modal = None

    async def start(self):
        self.modal = SailStartModal(self.cfg, self.sea_zh, self.local_tz)
        await self.interaction.response.send_modal(self.modal)
        is_timeout = await self.modal.wait()
        if is_timeout:
            return None

        self.submarine.instance.status = Status.SAIL

        self.submarine.instance.operator_info = OperatorInfo(self.interaction.user, None)
        self.submarine.instance.sail_info = SailInfo(
            Sea(self.modal.sea),
            self.modal.route,
            self.modal.end_dt.astimezone(self.local_tz),
        )
        self.submarine.instance.note = self.modal.note

        self.smgr.upsert_timer(self.submarine, self.after_countdown)


class SailEditor(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarine: ManagedSubmarine,
        smgr: Manager,
        sea_zh: dict[str, str],
        after_countdown: list[Callable],
    ):
        self.interaction = interaction
        self.submarine = submarine
        self.smgr = smgr
        self.sea_zh = sea_zh
        self.after_countdown = after_countdown

    async def start(self):
        sail_modal = SailEditModal(self.sea_zh, self.submarine)
        await self.interaction.response.send_modal(sail_modal)
        is_timeout = await sail_modal.wait()
        if is_timeout:
            return

        assert self.submarine.instance.operator_info is not None
        self.submarine.instance.operator_info.editor = self.interaction.user

        assert self.submarine.instance.sail_info is not None
        self.submarine.instance.sail_info.sea = Sea(sail_modal.sea)
        self.submarine.instance.sail_info.route = sail_modal.route
        self.submarine.instance.sail_info.return_dt = sail_modal.end_dt.astimezone(
            tz=self.submarine.instance.sail_info.return_dt.tzinfo
        )
        self.submarine.instance.note = sail_modal.note

        self.smgr.upsert_timer(self.submarine, self.after_countdown)


class ReturnChecker(Worker):
    def __init__(
        self,
        submarine: ManagedSubmarine,
    ):
        self.submarine = submarine

    async def start(self):
        self.submarine.instance.status = Status.RETURNED


class ConfirmChecker(Worker):
    def __init__(
        self,
        submarine: ManagedSubmarine,
    ):
        self.submarine = submarine

    async def start(self):
        self.submarine.instance.status = Status.IDLE

        self.submarine.instance.operator_info = None
        self.submarine.instance.sail_info = None


class CancelChecker(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarine: ManagedSubmarine,
        smgr: Manager,
    ):
        self.interaction = interaction
        self.submarine = submarine
        self.smgr = smgr

    async def start(self):
        await self.interaction.response.defer()

        self.submarine.instance.status = Status.IDLE

        self.submarine.instance.operator_info = None
        self.submarine.instance.sail_info = None
        self.smgr.cancel_timer(self.submarine)


class ConfigWorker(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        cfg: ConfigManager,
    ):
        self.interaction = interaction
        self.cfg = cfg

    async def start(self):
        config_modal = ConfigModal(self.cfg)
        await self.interaction.response.send_modal(config_modal)
        is_timeout = await config_modal.wait()
        if is_timeout:
            return

        self.cfg.announce_channel_id = config_modal.channel
        self.cfg.editors = config_modal.editors
        self.cfg.note_template = config_modal.note_template
        self.cfg.dump()


class RenameWorker(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        smgr: Manager,
    ):
        self.interaction = interaction
        self.smgr = smgr

    async def start(self):
        rename_modal = RenameModal(self.smgr)
        await self.interaction.response.send_modal(rename_modal)
        is_timeout = await rename_modal.wait()
        if is_timeout:
            return

        self.smgr.rename_all(rename_modal.submarine_names)


class FollowupMessageWorkerGroup:
    def __init__(
        self,
        bot: AraguBotBase,
        submarine_manager: Manager,
        cfg: ConfigManager,
    ):
        self.bot = bot
        self.smgr = submarine_manager
        self.cfg = cfg

    def get_writer(self, message: str, submarine: ManagedSubmarine):
        return FollowupMessageWorkerGroup.Writer(
            self.bot,
            self.cfg,
            message,
            submarine,
            self.smgr,
        )

    def get_cleaner(
        self, interaction: discord.Interaction, submarine: ManagedSubmarine, cleaned_message: str
    ):
        return FollowupMessageWorkerGroup.Cleaner(
            interaction,
            self.bot,
            self.cfg,
            cleaned_message,
            submarine,
            self.smgr,
        )

    class Writer(Worker):
        def __init__(
            self,
            bot: AraguBotBase,
            cfg: ConfigManager,
            message: str,
            submarine: ManagedSubmarine,
            smgr: Manager,
        ):
            self.bot = bot
            self.cid = cfg.announce_channel_id
            self.message = message
            self.submarine = submarine
            self.smgr = smgr

        async def start(self):
            announce_channel = self.bot.get_partial_messageable(self.cid)
            msg = await announce_channel.send(content=self.message)
            self.submarine.instance.followup_message_id = msg.id
            self.smgr.dump()

    class Cleaner(Worker):
        def __init__(
            self,
            interaction: discord.Interaction,
            bot: AraguBotBase,
            cfg: ConfigManager,
            cleaned_message: str,
            submarine: ManagedSubmarine,
            smgr: Manager,
        ):
            self.interaction = interaction
            self.bot = bot
            self.cid = cfg.announce_channel_id
            self.cleaned_message = cleaned_message
            self.submarine = submarine
            self.smgr = smgr

        async def start(self):
            announce_channel = self.bot.get_partial_messageable(self.cid)

            if self.submarine.followup_message_id is not None:
                msg = discord.PartialMessage(
                    channel=announce_channel,
                    id=self.submarine.followup_message_id,
                )

                await msg.delete()

            await announce_channel.send(
                content=self.cleaned_message,
                delete_after=12 * 60 * 60,  # keep the clean notice for 12 hours
            )
            self.submarine.instance.followup_message_id = None
            self.smgr.dump()
