import discord
from itemdict import ItemDict
from dcview.alias.enums import PanelOption
from dcview.protocol import ForwardInteraction


class AddButton(discord.ui.Button):
    def __init__(self, item_dict: ItemDict):
        super().__init__(
            label="新增",
            style=discord.ButtonStyle.success,
            emoji="➕",
        )

        self.item_dict = item_dict

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, PanelView)
        self.view.stop()
        self.view._option = PanelOption.ADD
        self.view.forward(interaction)


class DeleteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="移除",
            style=discord.ButtonStyle.danger,
            emoji="➖",
        )

    async def callback(self, interaction):
        await interaction.response.defer()
        # assert isinstance(self.view, MenuView)
        # self.view.update_next_view(DeleteAliasView())


class UpdateButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="更新",
            style=discord.ButtonStyle.blurple,
            emoji="✏️",
        )

    async def callback(self, interaction):
        await interaction.response.defer()
        # assert isinstance(self.view, MenuView)
        # self.view.update_next_view(UpdateAliasView())


class PanelView(discord.ui.LayoutView, ForwardInteraction):
    def __init__(self, item_dict: ItemDict):
        super().__init__()

        self.add_item(
            discord.ui.ActionRow(
                AddButton(item_dict),
                DeleteButton(),
                UpdateButton(),
            )
        )

        self._option = None

    @property
    def option(self) -> PanelOption | None:
        return self._option
