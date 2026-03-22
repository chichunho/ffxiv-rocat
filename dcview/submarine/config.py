import discord

from submarine.config import ConfigManager


class AnnounceChannelDropdown(discord.ui.Label):
    def __init__(self, cid: int | None):
        if cid is None:
            super().__init__(
                text="頻道",
                component=discord.ui.ChannelSelect(
                    required=True,
                    placeholder="選擇公告頻道",
                    channel_types=[discord.ChannelType.text],
                ),
            )
        else:
            super().__init__(
                text="公告頻道",
                component=discord.ui.ChannelSelect(
                    required=True,
                    default_values=[
                        discord.SelectDefaultValue(
                            id=cid,
                            type=discord.SelectDefaultValueType.channel,
                        )
                    ],
                    channel_types=[discord.ChannelType.text],
                ),
            )


class EditorListInput(discord.ui.Label):
    def __init__(self, editors: list[discord.User | discord.Member]):
        super().__init__(
            text="編輯者名單",
            component=discord.ui.TextInput(
                style=discord.TextStyle.long,
                default="\n".join([f"{editor.id}, {editor.display_name}" for editor in editors]),
                required=False,
            ),
        )


class NoteTemplate(discord.ui.Label):
    def __init__(self, content):
        super().__init__(
            text="登記備註格式",
            component=discord.ui.TextInput(
                style=discord.TextStyle.long,
                default=content,
                required=False,
            ),
        )


class ConfigModal(discord.ui.Modal):
    def __init__(self, cfg: ConfigManager):
        super().__init__(title="功能設定", timeout=180)

        self.cfg = cfg

        self._remind_channel_dropdown = AnnounceChannelDropdown(cfg.announce_channel_id)
        self.add_item(self._remind_channel_dropdown)

        self._editor_list_input = EditorListInput(cfg.fetched_editors)
        self.add_item(self._editor_list_input)

        self._note_template = NoteTemplate(cfg.note_template)
        self.add_item(self._note_template)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

    @property
    def channel(self) -> int:
        assert isinstance(self._remind_channel_dropdown.component, discord.ui.ChannelSelect)
        return self._remind_channel_dropdown.component.values[0].id

    @property
    def editors(self) -> list[int]:
        assert isinstance(self._editor_list_input.component, discord.ui.TextInput)
        return (
            []
            if len(self._editor_list_input.component.value) == 0
            else [
                int(x.split(",")[0].strip())
                for x in self._editor_list_input.component.value.split("\n")
            ]
        )

    @property
    def note_template(self) -> str:
        assert isinstance(self._note_template.component, discord.ui.TextInput)
        return self._note_template.component.value
