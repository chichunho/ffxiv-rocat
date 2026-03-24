from collections.abc import Iterable
from typing import Any

from submarine.enums import Sea


class SeaDict:
    def __init__(self, seadict: dict[str, Any]):
        self.seadict = seadict

    def is_node(self, node: str, sea: Sea) -> bool:
        return node in self.seadict.get(sea.value, {}).get("nodes", [])

    def get_zh_name(self, sea: Sea) -> str:
        return self.seadict.get(sea.value, {}).get("zh", "")

    def items(self) -> Iterable[tuple[str, str]]:
        for key, info in self.seadict.items():
            yield key, info["zh"]
