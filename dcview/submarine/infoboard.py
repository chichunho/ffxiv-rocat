import math
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, tzinfo

import discord
import pytz

from submarine.config import ConfigManager
from submarine.enums import Status
from submarine.manager import Manager as SubmarineManager
from submarine.model import ManagedSubmarine, SubmarineLike
from worker.submarine import (
    CancelChecker,
    ConfigWorker,
    ConfirmChecker,
    FollowupMessageWorkerGroup,
    RenameWorker,
    ReturnChecker,
    SailEditor,
    SailStarter,
)


class SubmarineName(discord.ui.TextDisplay):
    def __init__(self, name: str):
        super().__init__(content=f"## {name}")


class SailInfoDisplay(discord.ui.TextDisplay):
    def __init__(self, submarine: SubmarineLike, sea_zh: dict[str, str]):
        assert submarine.sail_info is not None

        time_left = submarine.sail_info.return_dt - datetime.now(pytz.utc)
        content = "\n".join(
            [
                f"海域: {sea_zh.get(submarine.sail_info.sea.value, 'N/A')}",
                f"航線: {' ➡️ '.join(submarine.sail_info.route)}",
                f"返航時間: {submarine.sail_info.return_dt.strftime('%m-%d %H:%M')}",
                f"剩餘時間: {'---' if submarine.status is Status.RETURNED else SailInfoDisplay.transform_timedelta(time_left)}",
            ]
        )
        super().__init__(content=content)

    @staticmethod
    def transform_timedelta(td: timedelta):
        if td.total_seconds() <= 0:
            return "---"
        else:
            tds = ""
            d = math.floor(td / timedelta(days=1))
            h = math.floor((td - timedelta(days=d)) / timedelta(hours=1))
            m = math.ceil((td - timedelta(days=d) - timedelta(hours=h)) / timedelta(minutes=1))
            if d > 0:
                tds += f"{d} 天 "
            if h > 0 or (d > 0 and m > 0):
                tds += f"{h} 小時 "
            if m > 0:
                tds += f"{m} 分鐘"

            return tds.strip()


class OperatorInfoDisplay(discord.ui.TextDisplay):
    def __init__(self, submarine: SubmarineLike):
        assert submarine.operator_info is not None
        content = "\n".join(
            [
                f"登記者: {submarine.operator_info.operator.display_name}",
                f"最後編輯: {'' if submarine.operator_info.editor is None else submarine.operator_info.editor.display_name}",
            ]
        )
        super().__init__(content=content)


class NoteDisplay(discord.ui.TextDisplay):
    def __init__(self, submarine: SubmarineLike):
        super().__init__(content=submarine.note)


class PublishButton(discord.ui.Button):
    def __init__(
        self,
        submarine: ManagedSubmarine,
        smgr: SubmarineManager,
        cfg: ConfigManager,
        sea_zh: dict[str, str],
        local_tz: tzinfo,
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label="登記出航",
            emoji="🌊",
            custom_id=f"ARAGU.Submarine.PublishButton.{submarine.name}",
        )
        self.submarine = submarine
        self.smgr = smgr
        self.cfg = cfg
        self.sea_zh = sea_zh
        self.local_tz = local_tz
        self.fmsg_workers = fmsg_workers

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, InfoBoardView)

        if not await self.view.permission_check(interaction.user):
            await interaction.response.defer()
            return

        after_countdown = AfterSubmarineReturn(
            self.view,
            self.submarine,
            self.fmsg_workers,
        ).callback

        next_worker = SailStarter(
            interaction,
            self.submarine,
            self.smgr,
            self.cfg,
            self.sea_zh,
            self.local_tz,
            after_countdown,
        )
        is_accepted = await self.smgr.exclusive_update(
            interaction.user,
            self.submarine,
            next_worker,
        )
        if not is_accepted:
            await interaction.response.send_message(
                content="有其他人正在更新此潛艇, 請稍後再試",
                ephemeral=True,
            )
            return

        await self.view.update()


class EditButton(discord.ui.Button):
    def __init__(
        self,
        submarine: ManagedSubmarine,
        smgr: SubmarineManager,
        sea_zh: dict[str, str],
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        super().__init__(
            style=discord.ButtonStyle.grey,
            label="編輯",
            emoji="✏️",
            custom_id=f"ARAGU.Submarine.EditButton.{submarine.name}",
        )
        self.submarine = submarine
        self.smgr = smgr
        self.sea_zh = sea_zh
        self.fmsg_workers = fmsg_workers

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, InfoBoardView)

        if not await self.view.permission_check(interaction.user):
            await interaction.response.defer()
            return

        after_countdown = AfterSubmarineReturn(
            self.view,
            self.submarine,
            self.fmsg_workers,
        ).callback

        next_worker = SailEditor(
            interaction,
            self.submarine,
            self.smgr,
            self.sea_zh,
            after_countdown,
        )
        is_accepted = await self.smgr.exclusive_update(
            interaction.user,
            self.submarine,
            next_worker,
        )
        if not is_accepted:
            await interaction.response.send_message(
                content="有其他人正在更新此潛艇, 請稍後再試",
                ephemeral=True,
            )
            return
        await self.view.update()


class CancelButton(discord.ui.Button):
    def __init__(self, submarine: ManagedSubmarine, smgr: SubmarineManager):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="取消",
            emoji="❌",
            custom_id=f"ARAGU.Submarine.CancelButton.{submarine.name}",
        )
        self.submarine = submarine
        self.smgr = smgr

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, InfoBoardView)
        if not await self.view.permission_check(interaction.user):
            await interaction.response.defer()
            return
        next_worker = CancelChecker(interaction, self.submarine, self.smgr)
        is_accepted = await self.smgr.exclusive_update(
            interaction.user,
            self.submarine,
            next_worker,
        )
        if not is_accepted:
            await interaction.response.send_message(
                content="有其他人正在更新此潛艇, 請稍後再試",
                ephemeral=True,
            )
            return
        await self.view.update()


class FinishButton(discord.ui.Button):
    def __init__(
        self,
        submarine: ManagedSubmarine,
        smgr: SubmarineManager,
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="確認收穫",
            emoji="🧳",
            custom_id=f"ARAGU.Submarine.FinishButton.{submarine.name}",
        )
        self.submarine = submarine
        self.smgr = smgr
        self.fmsg_workers = fmsg_workers

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, InfoBoardView)
        if not await self.view.permission_check(interaction.user):
            await interaction.response.defer()
            return
        next_worker = ConfirmChecker(self.submarine)
        is_accepted = await self.smgr.exclusive_update(
            interaction.user,
            self.submarine,
            next_worker,
        )
        if not is_accepted:
            await interaction.response.send_message(
                content="有其他人正在更新此潛艇, 請稍後再試",
                ephemeral=True,
            )
            return

        cleaner = self.fmsg_workers.get_cleaner(
            interaction,
            self.submarine,
            f"{interaction.user.display_name} 確認了潛水艇 **{self.submarine.name}** 的收穫",
        )
        await cleaner.start()

        await self.view.update()


class ConfigButton(discord.ui.Button):
    def __init__(
        self,
        smgr: SubmarineManager,
        cfg: ConfigManager,
    ):
        super().__init__(
            label="設定",
            emoji="⚙️",
            custom_id="ARAGU.Submarine.ConfigButton",
        )

        self.smgr = smgr
        self.cfg = cfg

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, InfoBoardView)
        if not await self.view.permission_check(interaction.user):
            await interaction.response.defer()
            return
        next_worker = ConfigWorker(interaction, self.cfg)
        await next_worker.start()
        await self.cfg.fetch_editors()
        await self.view.update()


class RefreshViewButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label="重新整理",
            emoji="🔄",
            custom_id="ARAGU.Submarine.RefreshViewButton",
        )

    async def callback(self, interaction):
        await interaction.response.defer()
        assert isinstance(self.view, InfoBoardView)
        await self.view.update()


class RenameButton(discord.ui.Button):
    def __init__(self, smgr):
        super().__init__(
            style=discord.ButtonStyle.grey,
            label="潛艇命名",
            emoji="🏷️",
            custom_id="ARAGU.Submarine.RenameButton",
        )

        self.smgr = smgr

    async def callback(self, interaction):
        assert isinstance(self.view, InfoBoardView)
        if not await self.view.permission_check(interaction.user):
            await interaction.response.defer()
            return
        next_worker = RenameWorker(interaction, self.smgr)
        await next_worker.start()
        await self.view.update()


class IdleLayout(discord.ui.Container):
    def __init__(
        self,
        submarine: ManagedSubmarine,
        smgr: SubmarineManager,
        cfg: ConfigManager,
        sea_zh: dict[str, str],
        local_tz: tzinfo,
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        super().__init__(accent_colour=discord.Colour.ash_embed())

        self.title = SubmarineName(submarine.name)
        self.publish_btn = PublishButton(submarine, smgr, cfg, sea_zh, local_tz, fmsg_workers)

        self.add_item(self.title)
        self.add_item(discord.ui.Separator())
        self.add_item(
            discord.ui.ActionRow(
                self.publish_btn,
            )
        )


class SailLayout(discord.ui.Container):
    def __init__(
        self,
        submarine: ManagedSubmarine,
        smgr: SubmarineManager,
        sea_zh: dict[str, str],
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        super().__init__(accent_colour=discord.Colour.blue())

        self.title = SubmarineName(submarine.name)
        self.add_item(self.title)
        self.add_item(discord.ui.Separator())

        self.sail_info = SailInfoDisplay(submarine, sea_zh)

        self.user_info = OperatorInfoDisplay(submarine)

        self.note = NoteDisplay(submarine)

        self.edit_btn = EditButton(submarine, smgr, sea_zh, fmsg_workers)
        self.cancel_btn = CancelButton(submarine, smgr)

        self.add_item(self.sail_info)
        self.add_item(self.user_info)
        self.add_item(discord.ui.Separator())
        if len(submarine.note) > 0:
            self.note = NoteDisplay(submarine)
            self.add_item(self.note)
            self.add_item(discord.ui.Separator())
        self.add_item(
            discord.ui.ActionRow(
                self.edit_btn,
                self.cancel_btn,
            )
        )


class ReturnedLayout(discord.ui.Container):
    def __init__(
        self,
        submarine: ManagedSubmarine,
        smgr: SubmarineManager,
        sea_zh: dict[str, str],
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        super().__init__(accent_colour=discord.Colour.brand_green())

        self.title = SubmarineName(submarine.name)
        self.add_item(self.title)
        self.add_item(discord.ui.Separator())

        self.sail_info = SailInfoDisplay(submarine, sea_zh)
        self.add_item(self.sail_info)

        self.user_info = OperatorInfoDisplay(submarine)
        self.add_item(self.user_info)

        self.add_item(discord.ui.Separator())

        if len(submarine.note) > 0:
            self.note = NoteDisplay(submarine)
            self.add_item(self.note)
            self.add_item(discord.ui.Separator())

        self.finish_btn = FinishButton(submarine, smgr, fmsg_workers)
        self.add_item(discord.ui.ActionRow(self.finish_btn))


class InfoBoardView(discord.ui.LayoutView):
    def __init__(
        self,
        submarine_manager: SubmarineManager,
        submarine_config: ConfigManager,
        sea_zh: dict[str, str],
        local_tz: tzinfo,
        permission_check: Callable[[discord.User | discord.Member], Awaitable[bool]],
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        super().__init__(timeout=None)

        self.smgr = submarine_manager
        self.cfg = submarine_config
        self.sea_zh = sea_zh
        self.local_tz = local_tz
        self.permission_check = permission_check
        self.fmsg_workers = fmsg_workers

        self.refresh_btn = RefreshViewButton()
        self.config_btn = ConfigButton(submarine_manager, submarine_config)
        self.rename_btn = RenameButton(submarine_manager)
        self.create_board()

    def create_board(self):
        self.add_item(
            discord.ui.ActionRow(
                self.refresh_btn,
                self.rename_btn,
                self.config_btn,
            )
        )

        self.add_item(discord.ui.Separator())

        for submarine in self.smgr.submarines:
            match submarine.status:
                case Status.IDLE:
                    self.add_item(
                        IdleLayout(
                            submarine,
                            self.smgr,
                            self.cfg,
                            self.sea_zh,
                            self.local_tz,
                            self.fmsg_workers,
                        )
                    )
                case Status.SAIL:
                    self.add_item(
                        SailLayout(
                            submarine,
                            self.smgr,
                            self.sea_zh,
                            self.fmsg_workers,
                        )
                    )
                case Status.RETURNED:
                    self.add_item(
                        ReturnedLayout(
                            submarine,
                            self.smgr,
                            self.sea_zh,
                            self.fmsg_workers,
                        )
                    )

    def set_message(self, message: discord.Message):
        self.message = message

    async def update(self):
        self.clear_items().create_board()
        await self.message.edit(view=self)


class AfterSubmarineReturn:
    def __init__(
        self,
        view: InfoBoardView,
        submarine: ManagedSubmarine,
        fmsg_workers: FollowupMessageWorkerGroup,
    ):
        self.submarine = submarine
        self.view = view
        self.fmsg_workers = fmsg_workers

    @property
    def callback(self) -> list[Callable[[], Awaitable[None]]]:
        writer = self.fmsg_workers.get_writer(
            f"潛水艇 {self.submarine.name} 已經返回, 請檢查收穫!",
            self.submarine,
        )
        return [ReturnChecker(self.submarine).start, self.view.update, writer.start]


class RegularInfoBoardUpdate:
    def __init__(self, view: InfoBoardView):
        self.view = view

    @property
    def callback(self):
        return self.view.update
