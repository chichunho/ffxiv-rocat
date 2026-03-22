from functools import total_ordering
from typing import NamedTuple, Protocol

type ItemName = str
type ItemCode = str
type ItemAliasName = str


class Item(NamedTuple):
    code: ItemCode
    name: ItemName


class ItemLike(Protocol):
    @property
    def code(self) -> ItemCode: ...

    @property
    def name(self) -> ItemName: ...


@total_ordering
class ScoredItem(ItemLike):
    def __init__(self, item: Item, distance_score: float, target_length: int):
        self.item = item
        self.distance_score = distance_score
        self.length_diff = abs(len(item.name) - target_length)

    @property
    def name(self):
        return self.item.name

    @property
    def code(self):
        return self.item.code

    def __lt__(self, another_item):
        if self.distance_score != another_item.distance_score:
            return self.distance_score < another_item.distance_score
        elif self.length_diff != another_item.length_diff:
            return self.length_diff < another_item.length_diff
        else:
            return self.name < another_item.name

    def __eq__(self, another_item):
        return self.item.name == another_item.item.name
