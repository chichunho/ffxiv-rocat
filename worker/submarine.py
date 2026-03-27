from collections.abc import Callable

import discord
from pytz import BaseTzInfo

from base import AraguBotBase
from dcview.submarine.config import ConfigModal
from dcview.submarine.modal import SailEditModal, SailStartModal
from dcview.submarine.rename import RenameModal
from submarine.config import ConfigManager
from submarine.enums import Status
from submarine.model import FollowupMessage, OperatorInfo, SailInfo
from submarine.seadict import SeaDict
from submarine.submarine import ManagedSubmarine
from utils.cache import DiscordGuildCache
from worker.worker import CancellableWorker, Worker


class SailStarter(CancellableWorker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarine: ManagedSubmarine,
        cfg: ConfigManager,
        sea_zh: SeaDict,
        local_tz: BaseTzInfo,
        after_countdown: list[Callable],
    ):
        self.interaction = interaction
        self.submarine = submarine
        self.cfg = cfg
        self.sea_zh = sea_zh
        self.local_tz = local_tz
        self.after_countdown = after_countdown
        self.modal: SailStartModal | None = None

    async def start(self):
        self.modal = SailStartModal(self.cfg, self.sea_zh, self.local_tz)
        await self.interaction.response.send_modal(self.modal)
        is_timeout = await self.modal.wait()
        if is_timeout or self.modal.is_cancelled:
            return

        # the interatcion must come from the guild
        assert isinstance(self.interaction.user, discord.Member)

        with self.submarine.update_ctx():
            self.submarine.replace(
                status=Status.SAIL,
                operator_info=OperatorInfo(
                    self.interaction.user,
                    None,
                ),
                sail_info=SailInfo(
                    self.modal.sea,
                    self.modal.route,
                    self.modal.return_dt,
                ),
                note=self.modal.note,
            )

        self.submarine.upsert_return_countdown(self.after_countdown)

    def cancel(self):
        if self.modal is not None:
            self.modal.cancel()


class SailEditor(CancellableWorker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarine: ManagedSubmarine,
        seadict: SeaDict,
        local_tz: BaseTzInfo,
        after_countdown: list[Callable],
    ):
        self.interaction = interaction
        self.submarine = submarine
        self.seadict = seadict
        self.local_tz = local_tz
        self.after_countdown = after_countdown

        self.modal: SailEditModal | None = None

    async def start(self):
        self.modal = SailEditModal(self.seadict, self.submarine, self.local_tz)
        await self.interaction.response.send_modal(self.modal)
        is_timeout = await self.modal.wait()
        if is_timeout or self.modal.is_cancelled:
            return

        assert self.submarine.operator_info is not None
        assert isinstance(self.interaction.user, discord.Member)
        assert self.submarine.sail_info is not None

        with self.submarine.update_ctx():
            self.submarine.replace(
                operator_info=OperatorInfo(
                    self.submarine.operator_info.operator, self.interaction.user
                ),
                sail_info=SailInfo(
                    self.modal.sea,
                    self.modal.route,
                    self.modal.return_dt,
                ),
                note=self.modal.note,
            )

        self.submarine.upsert_return_countdown(self.after_countdown)

    def cancel(self):
        if self.modal is not None:
            self.modal.cancel()


class ReturnChecker(Worker):
    def __init__(
        self,
        submarine: ManagedSubmarine,
    ):
        self.submarine = submarine

    async def start(self):
        with self.submarine.update_ctx():
            self.submarine.replace(status=Status.RETURNED)


class ConfirmChecker(Worker):
    def __init__(
        self,
        submarine: ManagedSubmarine,
    ):
        self.submarine = submarine

    async def start(self):
        with self.submarine.update_ctx():
            self.submarine.clear(operator_info=True, sail_info=True)
            self.submarine.replace(status=Status.IDLE)


class CancelChecker(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarine: ManagedSubmarine,
    ):
        self.interaction = interaction
        self.submarine = submarine

    async def start(self):
        await self.interaction.response.defer()

        with self.submarine.update_ctx():
            self.submarine.clear(operator_info=True, sail_info=True)
            self.submarine.replace(status=Status.IDLE)
            self.submarine.cancel_return_countdown()


class ConfigWorker(CancellableWorker):
    def __init__(
        self,
        interaction: discord.Interaction,
        cfg: ConfigManager,
        guild_cache: DiscordGuildCache,
    ):
        self.interaction = interaction
        self.cfg = cfg
        self.guild_cache = guild_cache

    async def start(self):
        editors = await self.guild_cache.get_memebers(self.cfg.editor_ids)
        self.modal = ConfigModal(self.cfg, editors)
        await self.interaction.response.send_modal(self.modal)
        is_timeout = await self.modal.wait()
        if is_timeout or self.modal.is_cancelled:
            return

        self.cfg.announce_channel_id = self.modal.channel_id
        self.cfg.editor_ids = self.modal.editor_ids
        self.cfg.note_template = self.modal.note_template
        self.cfg.dump()

    def cancel(self):
        if self.modal is not None:
            self.modal.cancel()


class RenameWorker(CancellableWorker):
    def __init__(
        self,
        interaction: discord.Interaction,
        submarines: list[ManagedSubmarine],
    ):
        self.interaction = interaction
        self.submarines = submarines

    async def start(self):

        self.modal = RenameModal(self.submarines)
        await self.interaction.response.send_modal(self.modal)
        is_timeout = await self.modal.wait()
        if is_timeout or self.modal.is_cancelled:
            return

        # use a hack to reduce the file I/O
        # since all 4 submarine states are stored in a single file
        # if dump them seperately it will produce 4 I/O cost
        # however if we sure that 4 submarine are managed by the same manager (which it should be)
        # we can directly dump once by calling submarine.manager.dump
        shared_man = self.submarines[0].manager
        for submarine in self.submarines:
            if submarine.manager is not shared_man:
                shared_man = None
                break

        if shared_man is not None:
            for idx, new_name in enumerate(self.modal.submarine_names):
                self.submarines[idx].replace(name=new_name)
            shared_man.dump()
        else:
            for new_name, submarine in zip(self.modal.submarine_names, self.submarines):
                with submarine.update_ctx():
                    submarine.replace(name=new_name)

    def cancel(self):
        if self.modal is not None:
            self.modal.cancel()


class FollowupMessageWorkerGroup:
    def __init__(
        self,
        bot: AraguBotBase,
        cfg: ConfigManager,
    ):
        self.bot = bot
        self.cfg = cfg

    def get_writer(self, message: str, submarine: ManagedSubmarine):
        return FollowupMessageWorkerGroup.Writer(
            self.bot,
            self.cfg,
            message,
            submarine,
        )

    def get_cleaner(
        self,
        interaction: discord.Interaction,
        submarine: ManagedSubmarine,
        cleaned_message: str,
    ):
        return FollowupMessageWorkerGroup.Cleaner(
            interaction,
            self.bot,
            self.cfg,
            cleaned_message,
            submarine,
        )

    class Writer(Worker):
        def __init__(
            self,
            bot: AraguBotBase,
            cfg: ConfigManager,
            message: str,
            submarine: ManagedSubmarine,
        ):
            self.bot = bot
            self.cfg = cfg
            self.message = message
            self.submarine = submarine

        async def start(self):
            # the announce channel is at least the default -> the command init channel, should not be None
            assert self.cfg.announce_channel_id is not None
            announce_channel = self.bot.get_partial_messageable(
                self.cfg.announce_channel_id
            )

            try:
                msg = await announce_channel.send(content=self.message)

                with self.submarine.update_ctx():
                    self.submarine.replace(
                        followup_message=FollowupMessage(msg.channel.id, msg.id)
                    )

            except (discord.NotFound, discord.HTTPException, discord.Forbidden) as e:
                print(e)
                pass
                # if the message failed to send, just ignore it

    class Cleaner(Worker):
        def __init__(
            self,
            interaction: discord.Interaction,
            bot: AraguBotBase,
            cfg: ConfigManager,
            cleaned_message: str,
            submarine: ManagedSubmarine,
        ):
            self.interaction = interaction
            self.bot = bot
            # the followup message is sent, the announce channel should not be None
            self.cfg = cfg
            self.cleaned_message = cleaned_message
            self.submarine = submarine

        async def start(self):
            try:
                if self.submarine.followup_message is not None:
                    msg = discord.PartialMessage(
                        channel=self.bot.get_partial_messageable(
                            self.submarine.followup_message.channel_id
                        ),
                        id=self.submarine.followup_message.message_id,
                    )

                    await msg.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                print(e)
                pass
                # if the followup messsage actions failed, it does not affect the main control flow,
                # afterall, the message can be deleted by guild admin

            try:
                assert self.cfg.announce_channel_id is not None
                announce_channel = self.bot.get_partial_messageable(
                    self.cfg.announce_channel_id
                )
                await announce_channel.send(
                    content=self.cleaned_message,
                    delete_after=12 * 60 * 60,  # keep the clean notice for 12 hours
                )
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                print(e)
                pass
                # this does not affect the main control flow,
                # the missing message can be entered manually

            with self.submarine.update_ctx():
                self.submarine.clear(followup_message=True)
