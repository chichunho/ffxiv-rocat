import discord

from dcview.enums import ReplyOption
from dcview.protocol import ItemSearchForm
from market.enums import AdvancedSearchOption

from dcview.common import (
    ItemMasterKeywordTextInput,
    ItemFilterKeywordTextInput,
    ItemSearchOptionCheckboxGroup,
    ReplyOptionRadioGroup,
)


class ItemSearchView(discord.ui.Modal, ItemSearchForm):
    def __init__(self):
        super().__init__(title="新別名要給...")

    _master_keyword = ItemMasterKeywordTextInput()
    _filter_keyword = ItemFilterKeywordTextInput()

    _search_options = ItemSearchOptionCheckboxGroup()
    _reply_options = ReplyOptionRadioGroup()

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

    @property
    def master_keyword(self):
        assert isinstance(self._master_keyword.component, discord.ui.TextInput)
        return self._master_keyword.component.value

    @property
    def filter_keyword(self):
        assert isinstance(self._filter_keyword.component, discord.ui.TextInput)
        return self._filter_keyword.component.value

    @property
    def search_options(self):
        assert isinstance(self._search_options.component, discord.ui.CheckboxGroup)
        return set(
            [AdvancedSearchOption(val) for val in self._search_options.component.values]
        )

    @property
    def reply_option(self):
        assert isinstance(self._reply_options.component, discord.ui.RadioGroup)
        return ReplyOption(self._reply_options.component.value)
