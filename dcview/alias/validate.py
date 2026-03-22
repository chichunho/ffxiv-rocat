import discord
from dcview.protocol import ForwardInteraction


class _ContinueButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="下一步")

    async def callback(self, interaction):
        assert isinstance(self.view, ContinueView)
        self.view.stop()
        await interaction.delete_original_response()
        self.view.forward(interaction)


class ContinueButton(discord.ui.ActionRow):
    def __init__(self):
        super().__init__(_ContinueButton())


class ContinueView(discord.ui.LayoutView, ForwardInteraction):
    def __init__(self):
        super().__init__()

        _msg = discord.ui.TextDisplay(content="新別名可以使用! 請點擊下一步繼續...")
        _btn = ContinueButton()

        self.add_item(_msg)
        self.add_item(_btn)


class FailView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()

        self.add_item(
            discord.ui.TextDisplay(content="已有相同的別名, 請選擇另一個別名")
        )


class ValidateView(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="新別名")

    _new_alias = discord.ui.Label(
        text="別名",
        description="不能包含萬用字符(*)",
        component=discord.ui.TextInput(),
    )

    @property
    def new_alias(self):
        assert isinstance(self._new_alias.component, discord.ui.TextInput)
        return self._new_alias.component.value

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
