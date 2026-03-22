import discord
from itemdict.model import Item


class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="確認")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        assert isinstance(self.view, AddAliasView)
        self.view.stop()
        await interaction.delete_original_response()


class ItemDropdown(discord.ui.ActionRow):
    def __init__(self, items: list[Item]):
        options = [
            discord.SelectOption(label=item.name, value=item.code) for item in items
        ]
        self.choices = {item.code: item.name for item in items}

        super().__init__()

        self.dropdown = discord.ui.Select(
            placeholder="選擇物品...",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )

        self.add_item(self.dropdown)

    @property
    def value(self) -> str:
        return self.dropdown.values[0]


class AddAliasView(discord.ui.LayoutView):
    def __init__(
        self,
        items: list[Item],
    ):
        super().__init__()

        self.dropdown = ItemDropdown(items)
        self.add_item(self.dropdown)

        confirm_btn = ConfirmButton()
        self.add_item(confirm_btn)
