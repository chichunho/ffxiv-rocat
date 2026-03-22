from datetime import datetime, tzinfo
from typing import Any

from itemdict import ItemDict
from market.universalis.response import ItemPrice as ItemPriceRecipe


class ItemPrice:
    def __init__(
        self,
        target_item_id: str,
        item_dict: ItemDict,
        world_dict: dict[str, str],
        local_tz: tzinfo,
    ):
        self.target_item_id = target_item_id
        self.item_dict = item_dict
        self.world_dict = world_dict
        self.local_tz = local_tz

    def __call__(self, raw_data: dict[str, Any] | None) -> dict[str, Any]:
        if raw_data is None:
            pre_data = {"id": self.target_item_id}
        else:
            pre_data = self._extract_from_raw(raw_data)
        return self._parse_from_pre(pre_data)

    def _extract_from_raw(self, raw_data: dict[str, Any]):
        # we should always expect raw_data is not None
        recipe = ItemPriceRecipe()
        return recipe(raw_data)

    def _parse_from_pre(self, pre_data: dict[str, Any]) -> dict[str, Any]:
        pre_data["name"] = self.item_dict.decode(str(pre_data["id"]))

        # the response is in error, only item id can be confirmed
        if "update_time" not in pre_data:
            return pre_data

        pre_data["update_time"] = (
            datetime.fromtimestamp(pre_data["update_time"] // 1000)
            .astimezone(self.local_tz)
            .strftime("%Y-%m-%d %H:%M")
        )

        # for world_stat in pre_soup["world_stats"].values():
        #     for q in ["nq", "hq"]:
        #         for t in ["min_per_unit", "min_total"]:
        #             if world_stat[q][t]["count"] >= 100:
        #                 world_stat[q][t]["count"] = "99+"
        #             else:
        #                 world_stat[q][t]["count"] = str(world_stat[q]["count"])

        pre_data["world_stats"] = {
            k: v
            for k, v in sorted(
                pre_data["world_stats"].items(),
                key=lambda x: x[1]["nq"]["min_per_unit"]["price"],
            )
        }
        pre_data["world_stats"] = {
            k: v
            for k, v in sorted(
                pre_data["world_stats"].items(),
                key=lambda x: x[1]["hq"]["min_per_unit"]["price"],
            )
        }

        return pre_data
