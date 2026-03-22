from typing import Protocol

import discord

from dcview.enums import ReplyOption
from market.enums import AdvancedSearchOption


class ItemSearchForm(Protocol):
    @property
    def master_keyword(self) -> str: ...

    @property
    def filter_keyword(self) -> str: ...

    @property
    def search_options(self) -> set[AdvancedSearchOption]: ...

    @property
    def reply_option(self) -> ReplyOption: ...


class ForwardInteraction:
    def forward(self, interaction: discord.Interaction):
        self._next_interaction = interaction

    @property
    def next_interaction(self) -> discord.Interaction:
        return self._next_interaction
