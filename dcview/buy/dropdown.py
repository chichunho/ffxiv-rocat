from urllib.parse import quote as url_encode

import discord

from itemdict import ItemDict
from itemdict.model import Item, ItemName


class ItemDropdown(discord.ui.Select):
    def __init__(self, items: list[Item]):
        options = [discord.SelectOption(label=item.name, value=item.code) for item in items]
        self.choices = {item.code: item.name for item in items}

        super().__init__(
            placeholder="選擇目標物品...",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        self.placeholder = self.choices[self.values[0]]

        assert isinstance(self.view, ItemDropdownView)
        self.view.selected_item = Item(self.values[0], self.choices[self.values[0]])
        self.view.update_buttons_prop()

        await interaction.response.edit_message(view=self.view)


class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="確認",
            row=2,
            disabled=True,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        assert isinstance(self.view, ItemDropdownView)
        self.view.stop()


class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="re-enter",
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class FavButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="收藏",
            emoji=discord.PartialEmoji(name="⭐"),
            disabled=True,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class InfoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="物品資訊 (灰機)",
            style=discord.ButtonStyle.link,
            disabled=True,
            row=2,
            url="https://ff14.huijiwiki.com/wiki",
        )

        self.info_url_template = "https://ff14.huijiwiki.com/wiki/{encoded_name}"

    def update_url(self, name: ItemName):
        self.url = self.info_url_template.format(
            encoded_name=url_encode(f"物品:{name}", encoding="utf-8")
        )


class ItemDropdownView(discord.ui.View):
    def __init__(self, items: list[Item], item_dict: ItemDict):
        super().__init__(timeout=60)

        self.item_dict = item_dict
        self.selected_item: Item | None = None

        self.dropdown = ItemDropdown(items)
        self.add_item(self.dropdown)

        self.confirm_btn = ConfirmButton()
        self.add_item(self.confirm_btn)

        self.info_btn = InfoButton()
        self.add_item(self.info_btn)

    def update_buttons_prop(self):
        assert self.selected_item is not None
        self.info_btn.update_url(self.item_dict.t2s(self.selected_item).name)
        self.confirm_btn.disabled = False
        self.info_btn.disabled = False
