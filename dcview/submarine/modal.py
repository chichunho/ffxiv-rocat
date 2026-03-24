from datetime import datetime

import discord
import pytz
from pytz import BaseTzInfo

from dcview.model import AwaredDatetime
from dcview.protocol import Cancellable
from submarine.config import ConfigManager
from submarine.enums import Sea
from submarine.seadict import SeaDict
from submarine.submarine import ManagedSubmarine


class SeaDropDown(discord.ui.Label):
    def __init__(self, sea_zh: SeaDict, default: Sea | None = None):
        options = []
        for val, zh_name in sea_zh.items():
            if default is not None and val == default.value:
                options.append(
                    discord.SelectOption(
                        label=zh_name,
                        value=val,
                        default=True,
                    )
                )
            else:
                options.append(
                    discord.SelectOption(
                        label=zh_name,
                        value=val,
                    )
                )

        super().__init__(
            text="海域",
            component=discord.ui.Select(
                placeholder="選擇海域",
                options=options,
            ),
        )


class RouteTextInput(discord.ui.Label):
    def __init__(self, default: list[str] | None = None):
        super().__init__(
            text="路線",
            description="請用 (,) 分隔",
            component=discord.ui.TextInput(
                default="" if default is None else ", ".join(default),
            ),
        )


class ReturnedDatetime(discord.ui.Label):
    def __init__(self, default: datetime):
        super().__init__(
            text="返航時間",
            description="請根據遊戲內顯示的格式輸入",
            component=discord.ui.TextInput(default=default.strftime("%Y/%m/%d %H:%M")),
        )


class NoteTextInput(discord.ui.Label):
    def __init__(self, default: str):
        super().__init__(
            text="備註",
            component=discord.ui.TextInput(
                default=default,
                required=False,
                style=discord.TextStyle.long,
            ),
        )


class SailStartModal(discord.ui.Modal, Cancellable):
    def __init__(
        self,
        cfg: ConfigManager,
        seadict: SeaDict,
        local_tz: BaseTzInfo,
    ):
        super().__init__(title="登記出航", timeout=180)

        self.seadict = seadict
        self.local_tz = local_tz

        self.sea_dropdown = SeaDropDown(seadict)
        self.route_input = RouteTextInput()
        self.return_input = ReturnedDatetime(datetime.now(local_tz))
        self.note_input = NoteTextInput(cfg.note_template)

        self._is_cancelled = False

        self.add_item(self.sea_dropdown)
        self.add_item(self.route_input)
        self.add_item(self.return_input)
        self.add_item(self.note_input)

    def cancel(self):
        self._is_cancelled = True
        self.stop()

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def sea(self) -> Sea:
        assert isinstance(self.sea_dropdown.component, discord.ui.Select)
        return Sea(self.sea_dropdown.component.values[0])

    @property
    def route(self) -> list[str]:
        assert isinstance(self.route_input.component, discord.ui.TextInput)
        return [s.strip().upper() for s in self.route_input.component.value.split(",")]

    @property
    def return_dt(self) -> AwaredDatetime:
        return self.local_tz.localize(self.tf_return_input)

    @property
    def note(self) -> str:
        assert isinstance(self.note_input.component, discord.ui.TextInput)
        return self.note_input.component.value

    async def on_submit(self, interaction: discord.Interaction):
        try:
            assert isinstance(self.return_input.component, discord.ui.TextInput)
            self.tf_return_input = datetime.strptime(
                self.return_input.component.value.strip(), "%Y/%m/%d %H:%M"
            )
        except ValueError:
            await interaction.response.send_message(
                content="返航時間輸入格式有誤",
                ephemeral=True,
            )
            self.cancel()
            return

        if self.return_dt <= datetime.now(pytz.utc):
            await interaction.response.send_message(
                "返航時間不能早於或等於目前時間", ephemeral=True
            )
            self.cancel()
            return

        for node in self.route:
            if not self.seadict.is_node(node, Sea(self.sea)):
                await interaction.response.send_message(
                    content=f"{self.seadict.get_zh_name(self.sea)}不存在航線節點 **{node}**",
                    ephemeral=True,
                )
                self.cancel()
                return

        await interaction.response.defer()


class SailEditModal(discord.ui.Modal, Cancellable):
    def __init__(
        self, seadict: SeaDict, submarine: ManagedSubmarine, local_tz: BaseTzInfo
    ):
        super().__init__(title="編輯航行資料", timeout=60)

        assert submarine.sail_info is not None

        self.seadict = seadict
        self.local_tz = local_tz

        self.sea_dropdown = SeaDropDown(seadict, default=submarine.sail_info.sea)

        self.route_input = RouteTextInput(default=submarine.sail_info.route)

        self.return_input = ReturnedDatetime(default=submarine.sail_info.return_dt)

        self.note_input = NoteTextInput(submarine.note)

        self._is_cancelled = False

        self.add_item(self.sea_dropdown)
        self.add_item(self.route_input)
        self.add_item(self.return_input)
        self.add_item(self.note_input)

    def cancel(self):
        self._is_cancelled = True
        self.stop()

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def sea(self) -> Sea:
        assert isinstance(self.sea_dropdown.component, discord.ui.Select)
        return Sea(self.sea_dropdown.component.values[0])

    @property
    def route(self) -> list[str]:
        assert isinstance(self.route_input.component, discord.ui.TextInput)
        return [s.strip().upper() for s in self.route_input.component.value.split(",")]

    @property
    def return_dt(self) -> AwaredDatetime:
        return self.local_tz.localize(self.tf_return_input)

    @property
    def note(self) -> str:
        assert isinstance(self.note_input.component, discord.ui.TextInput)
        return self.note_input.component.value

    async def on_submit(self, interaction: discord.Interaction):
        try:
            assert isinstance(self.return_input.component, discord.ui.TextInput)
            self.tf_return_input = datetime.strptime(
                self.return_input.component.value.strip(), "%Y/%m/%d %H:%M"
            )
        except ValueError:
            await interaction.response.send_message(
                content="返航時間輸入格式有誤",
                ephemeral=True,
            )
            self.cancel()
            return

        if self.return_dt <= datetime.now(pytz.utc):
            await interaction.response.send_message(
                "返航時間不能早於或等於目前時間", ephemeral=True
            )
            self.cancel()
            return

        for node in self.route:
            if not self.seadict.is_node(node, Sea(self.sea)):
                await interaction.response.send_message(
                    content=f"{self.seadict.get_zh_name(self.sea)}不存在航線節點 **{node}**",
                    ephemeral=True,
                )
                self.cancel()
                return

        await interaction.response.defer()
