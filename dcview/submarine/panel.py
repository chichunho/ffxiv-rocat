import discord
from dcview.submarine.enums import PanelOption
from dcview.protocol import ForwardInteraction


class ConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="設定",
            emoji="⚙️",
        )

    async def callback(self, interaction):
        assert isinstance(self.view, PanelView)
        self.view.stop()
        self.view._option = PanelOption.CONFIG
        self.view.forward(interaction)


class DepartureButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="登記出航",
            emoji="🌊",
        )


class StatusButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label="查看航行",
            emoji="📝",
        )


class AddRemindButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="返航通知",
            emoji="🔔",
        )


class DeleteRemindButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="取消通知",
            emoji="🔕",
        )


class PanelView(discord.ui.LayoutView, ForwardInteraction):
    def __init__(self):
        super().__init__()

        self._option = None

        self.config_btn = ConfigButton()

        self.departure_btn = DepartureButton()
        self.status_btn = StatusButton()

        self.add_remind_btn = AddRemindButton()
        self.del_remind_btn = DeleteRemindButton()

        self.add_item(
            discord.ui.Container(
                discord.ui.ActionRow(
                    self.departure_btn,
                    self.status_btn,
                ),
            )
        )

        self.add_item(
            discord.ui.Container(
                discord.ui.ActionRow(
                    self.add_remind_btn,
                    self.del_remind_btn,
                ),
            )
        )

        self.add_item(
            discord.ui.Container(
                discord.ui.ActionRow(
                    self.config_btn,
                ),
            )
        )

    @property
    def value(self) -> PanelOption:
        return self._option
