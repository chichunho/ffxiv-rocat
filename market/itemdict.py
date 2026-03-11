import heapq
from collections import UserDict
from typing import Callable, Iterable

from bidict import bidict
from rapidfuzz import fuzz as fuzz
from rapidfuzz.process import extract as fuzzy_extract
from rapidfuzz.process import extract_iter as fuzzy_extract_iter

from market.model import Item, ItemAliasName, ItemCode, ItemName, ScoredItem
from market.search import AdvancedChecker, AdvancedSearchOption, ItemKeyword
from utils.orderedset import SimpleOrderedSet


class ItemDict(UserDict):
    def __init__(
        self,
        default_dict: dict[ItemCode, ItemName],
        alias_dict: dict[ItemAliasName, ItemCode],
        fuzzy_dict: dict[str, ItemName],
        sc_dict: dict[ItemCode, ItemName],
    ):
        self.data = default_dict

        # bi-directional
        self.default_dict = bidict(default_dict)
        self.alias_dict = alias_dict
        self.fuzzy_dict = fuzzy_dict
        self.sc_dict = sc_dict

    def _fuzzy_search(
        self,
        keyword: str,
        limit: int | None = 10,
        case_insensitive=False,
    ) -> Iterable[Item | ScoredItem]:
        if limit is None:
            for _, score, code in fuzzy_extract_iter(keyword, self, score_cutoff=70):
                yield ScoredItem(
                    Item(
                        code,
                        self.decode(code).lower()
                        if case_insensitive
                        else self.decode(code),
                    ),
                    score,
                    len(keyword),
                )
        else:
            yield from SimpleOrderedSet(
                [
                    Item(
                        code,
                        self.decode(code).lower()
                        if case_insensitive
                        else self.decode(code),
                    )
                    for _, _, code in fuzzy_extract(
                        keyword, self, limit=limit, score_cutoff=50
                    )
                ]
            )

    @staticmethod
    def hill_ordered(
        keyword_length: int, items: Iterable[Item], reverse=False
    ) -> list[Item]:
        return sorted(
            items,
            reverse=reverse,
            key=lambda x: (
                (len(x.name) - keyword_length - 100)
                if keyword_length <= len(x[1])
                else abs(keyword_length - len(x.name))
            ),
        )

    def items(self):
        yield from self.default_dict.items()

        for name, code in self.alias_dict.items():
            yield code, name

        yield from self.fuzzy_dict.items()

    def search(
        self,
        keyword: ItemKeyword,
        case_insensitive=False,
        limit: int = 25,
        ordered: Callable[[int, Iterable[Item]], list[Item]] | None = hill_ordered,
        check_options: Iterable[AdvancedSearchOption] | None = None,
    ) -> list[Item]:
        # fuzzy match
        fuzzy_matches = []
        if check_options is None and len(keyword.filter_words) == 0:
            fuzzy_matches: Iterable[Item] = self._fuzzy_search(
                keyword.master, limit=limit, case_insensitive=case_insensitive
            )
        else:
            fuzzy_matches_iter: Iterable[ScoredItem] = self._fuzzy_search(
                keyword.master, limit=None, case_insensitive=case_insensitive
            )
            checker = AdvancedChecker(keyword, check_options)
            fuzzy_middle: list[ScoredItem] = []
            for scored_item in fuzzy_matches_iter:
                if not checker.check(scored_item):
                    continue
                if len(fuzzy_middle) < limit:
                    heapq.heappush(fuzzy_middle, scored_item)
                else:
                    heapq.heappushpop(fuzzy_middle, scored_item)
            fuzzy_matches = SimpleOrderedSet(
                [
                    Item(scored_item.code, self.decode(scored_item.code))
                    for scored_item in sorted(
                        fuzzy_middle, key=lambda x: x.distance_score, reverse=True
                    )
                ]
            )

        if ordered:
            return ordered(len(keyword), fuzzy_matches)
        else:
            return list(fuzzy_matches)

    def encode(self, key: ItemName | ItemCode) -> Item | None:
        # if key is num-like, treat it as item code
        try:
            int(key)
            return Item(key, self.decode(key))
        except ValueError:
            pass
        except KeyError:
            return None

        # for key is str-like, treat it as item name

        try:
            return Item(self.default_dict.inverse[key], key)
        except KeyError:
            pass

        try:
            return Item(self.alias_dict[key], self.decode(self.alias_dict[key]))
        except KeyError:
            pass

        try:
            if len(self.fuzzy_dict[key.lower()]) == 1:
                return Item(
                    self.fuzzy_dict[key][0],
                    self.decode(self.fuzzy_dict[key.lower()][0]),
                )
        except KeyError:
            pass

        return None

    def decode(self, code: ItemCode) -> ItemName:
        return self.default_dict[code]

    def add_alias(
        self,
        item: Item,
        alias_name: str,
        wildcard_char="*",
    ) -> tuple[bool, Item]:
        if wildcard_char in alias_name:
            return False, None
        if alias_name in self.default_dict.inverse:
            return False, Item(self.default_dict.inverse[alias_name], alias_name)
        if alias_name in self.alias_dict:
            return False, Item(self.alias_dict[alias_name], alias_name)

        self.alias_dict[alias_name] = item.code

        return True, Item(self.alias_dict[alias_name], alias_name)

    def is_perfect_keyword(self, keyword: ItemKeyword):
        result = self.encode(keyword.raw_master)
        if result is not None:
            return True

        result = self.search(keyword)
        if len(result) == 1 and result[0] is not None:
            return True

        return False

    def t2s(self, item: Item) -> Item:
        return Item(item.code, self.sc_dict[item.code])
