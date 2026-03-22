import discord

from dcview.common import (
    ItemFilterKeywordTextInput,
    ItemMasterKeywordTextInput,
    ItemSearchOptionCheckboxGroup,
    ReplyOptionRadioGroup,
)
from dcview.enums import ReplyOption
from dcview.protocol import ItemSearchForm
from market.enums import AdvancedSearchOption


class BuyModalView(discord.ui.Modal, ItemSearchForm):
    def __init__(self):
        super().__init__(title="繁中市場查價", timeout=180)

    _master_keyword = ItemMasterKeywordTextInput()

    _filter_keyword = ItemFilterKeywordTextInput()

    _is_single_direct_search = discord.ui.Label(
        text="選項唯一時直接查詢價格",
        component=discord.ui.Checkbox(default=True),
    )

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
        res = set([AdvancedSearchOption(val) for val in self._search_options.component.values])
        assert isinstance(self._is_single_direct_search.component, discord.ui.Checkbox)
        if self._is_single_direct_search.component.value:
            res.add(AdvancedSearchOption.OPT_SINGLE_IS_PERFECT)
        return res

    @property
    def reply_option(self):
        assert isinstance(self._reply_options.component, discord.ui.RadioGroup)
        return ReplyOption(self._reply_options.component.value)
