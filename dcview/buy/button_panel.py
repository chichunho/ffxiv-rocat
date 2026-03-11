import discord


class FavButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="收藏", emoji=discord.PartialEmoji(name="⭐"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class InfoButton(discord.ui.Button):
    def __init__(self, url: str):
        super().__init__(label="物品資訊", style=discord.ButtonStyle.link, url=url)


class ButtonRow(discord.ui.ActionRow):
    def __init__(self, info_url: str):
        super().__init__()

        self.add_item(FavButton())
        self.add_item(InfoButton(url=info_url))


class ItemPanelView(discord.ui.LayoutView):
    def __init__(self, info_url: str):
        super().__init__()

        self.add_item(ButtonRow(info_url))
