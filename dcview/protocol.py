from typing import Protocol
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
