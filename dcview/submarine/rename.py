import discord

from submarine.manager import Manager
from submarine.model import ManagedSubmarine


class NameTextInput(discord.ui.Label):
    def __init__(self, n: int, submarine: ManagedSubmarine):
        super().__init__(
            text=f"#{n} 潛艇",
            component=discord.ui.TextInput(default=submarine.name),
        )


class RenameModal(discord.ui.Modal):
    def __init__(self, smgr: Manager):
        super().__init__(title="潛艇重新命名", timeout=180)

        self._submarine_names: list[NameTextInput] = []
        for idx, submarine in enumerate(smgr.submarines, start=1):
            sname = NameTextInput(idx, submarine)
            self._submarine_names.append(sname)
            self.add_item(sname)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

    @property
    def submarine_names(self) -> list[str]:
        res: list[str] = []
        for s in self._submarine_names:
            assert isinstance(s.component, discord.ui.TextInput)
            res.append(s.component.value)
        return res
