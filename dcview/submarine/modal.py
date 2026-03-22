from datetime import datetime

import discord

from submarine.config import ConfigManager
from submarine.enums import Sea
from submarine.model import ManagedSubmarine


class SeaDropDown(discord.ui.Label):
    def __init__(self, sea_zh: dict[str, str], default: Sea | None = None):
        options = []
        for val, label in sea_zh.items():
            if default is not None and val == default.value:
                options.append(
                    discord.SelectOption(
                        label=label,
                        value=val,
                        default=True,
                    )
                )
            else:
                options.append(
                    discord.SelectOption(
                        label=label,
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
    def __init__(self, default: datetime | None = None):
        super().__init__(
            text="返航時間",
            description="請根據遊戲內顯示的格式輸入",
            component=discord.ui.TextInput(
                default="" if default is None else default.strftime("%Y/%m/%d %H:%M")
            ),
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


class SailStartModal(discord.ui.Modal):
    def __init__(self, cfg: ConfigManager, sea_zh: dict[str, str]):
        super().__init__(title="登記出航", timeout=180)

        self.sea_dropdown = SeaDropDown(sea_zh)
        self.route_input = RouteTextInput()
        self.return_input = ReturnedDatetime()
        self.note_input = NoteTextInput(cfg.note_template)

        self.add_item(self.sea_dropdown)
        self.add_item(self.route_input)
        self.add_item(self.return_input)
        self.add_item(self.note_input)

    @property
    def sea(self) -> str:
        assert isinstance(self.sea_dropdown.component, discord.ui.Select)
        return self.sea_dropdown.component.values[0]

    @property
    def route(self) -> list[str]:
        assert isinstance(self.route_input.component, discord.ui.TextInput)
        return [s.strip().upper() for s in self.route_input.component.value.split(",")]

    @property
    def end_dt(self) -> datetime:
        return self.tf_return_input

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
            await interaction.response.defer()
        except ValueError:
            await interaction.response.send_message(
                content="日期格式有誤, 請重新編輯",
                ephemeral=True,
            )


class SailEditModal(discord.ui.Modal):
    def __init__(self, sea_zh: dict[str, str], submarine: ManagedSubmarine):
        super().__init__(title="編輯航行資料", timeout=60)

        assert submarine.sail_info is not None

        self.sea_dropdown = SeaDropDown(sea_zh, default=submarine.sail_info.sea)

        self.route_input = RouteTextInput(default=submarine.sail_info.route)

        self.return_input = ReturnedDatetime(default=submarine.sail_info.return_dt)

        self.note_input = NoteTextInput(submarine.note)

        self.add_item(self.sea_dropdown)
        self.add_item(self.route_input)
        self.add_item(self.return_input)
        self.add_item(self.note_input)

    @property
    def sea(self) -> str:
        assert isinstance(self.sea_dropdown.component, discord.ui.Select)
        return self.sea_dropdown.component.values[0]

    @property
    def route(self) -> list[str]:
        assert isinstance(self.route_input.component, discord.ui.TextInput)
        return [s.strip().upper() for s in self.route_input.component.value.split(",")]

    @property
    def end_dt(self) -> datetime:
        return self.tf_return_input

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
            await interaction.response.defer()
        except ValueError:
            await interaction.response.send_message(
                content="日期格式有誤, 請重新編輯",
                ephemeral=True,
            )
