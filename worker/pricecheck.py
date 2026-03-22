from datetime import tzinfo
from functools import partial
from typing import Any

import discord

from dcview.buy.dropdown import InfoButton, ItemDropdownView
from dcview.buy.result import PriceResultView

# from botview.buy_modal import BuyModalView
# from botview.item_dropdown import ItemDropdownView
from dcview.buy.search import BuyModalView
from dcview.enums import ReplyOption
from itemdict import ItemDict
from itemdict.model import Item
from market.search import AdvancedSearchOption, ItemKeyword
from market.universalis.client import Client as MarketClient
from market.universalis.middleware import ItemPrice as ItemPriceMiddle
from worker.worker import Worker


class PriceChecker(Worker):
    def __init__(
        self,
        interaction: discord.Interaction,
        item_dict: ItemDict,
        world_dict: dict[str, str],
        http_session: Any,
        local_tz: tzinfo,
    ):
        self.interaction = interaction
        self.item_dict = item_dict
        self.world_dict = world_dict
        self.http_session = http_session
        self.local_tz = local_tz

    async def start(self):
        buy_modal = BuyModalView()
        await self.interaction.response.send_modal(buy_modal)

        is_timeout = await buy_modal.wait()
        if is_timeout:
            return

        keyword = ItemKeyword(
            buy_modal.master_keyword,
            buy_modal.filter_keyword,
        )

        # there may be no filter in initial, but new in processed keyword
        check_options = buy_modal.search_options
        if len(keyword.filter_words) > 0:
            check_options.add(AdvancedSearchOption.OPT_CONTAINS)

        target_item = self.item_dict.encode(keyword.raw_master)

        items: list[Item] = []
        if target_item is None:
            items = self.item_dict.search(
                keyword,
                check_options=check_options,
                case_insensitive=(AdvancedSearchOption.OPT_CASE_INSENSITIVE in check_options),
            )

            # single match treat as perfect match
            if AdvancedSearchOption.OPT_SINGLE_IS_PERFECT in check_options:
                target_item = items[0] if len(items) == 1 else None

        # dm the user or not
        if buy_modal.reply_option is ReplyOption.Direct:
            send_message = partial(
                self.interaction.user.send,
                delete_after=60,
            )
        else:
            send_message = partial(
                self.interaction.followup.send,
                wait=True,
                ephemeral=True,
            )

        # if encode return empty and no valid item choices
        if target_item is None and len(items) == 0:
            await send_message(
                content="類似的物品名稱不存在 / 不可交易, 請再次確認喵",
                ephemeral=True,
            )  # type: ignore
            return
        # if there are valid item choices but we are not sure which item the user want
        elif target_item is None:
            dropdown_view = ItemDropdownView(items, self.item_dict)
            msg = await send_message(view=dropdown_view)
            is_timeout = await dropdown_view.wait()
            if is_timeout:
                await msg.delete()
                return
            else:
                target_item = self.item_dict.encode(dropdown_view.dropdown.values[0])
                assert target_item is not None
                await msg.delete()

        loading_msg = await send_message(content="正在搜尋資料喵...")

        response_data = await self._fetch_item(self._make_api_params(target_item.code))
        # embed_content = ItemPriceEmbed(response_data).message()
        info_btn = InfoButton()
        info_btn.update_url(self.item_dict.t2s(target_item).name)
        info_btn.disabled = False
        buy_result_view = PriceResultView(response_data, info_btn)

        await loading_msg.delete()
        # await send_message(embed=embed_content)
        await send_message(view=buy_result_view)

    def _make_api_params(self, item_id: str):
        params = {
            "item_ids": [item_id],
            "location": "陸行鳥",
            "hq": None,
            "listings": None,
            "sale_entries": 0,
            "stats_within": None,
            "sale_entries_within": None,
            "fields": [
                "itemID",
                "lastUploadTime",
                "listings.pricePerUnit",
                "listings.quantity",
                "listings.worldName",
                "listings.hq",
                "listings.total",
                # "listings.tax",
                "currentAveragePriceNQ",
                "currentAveragePriceHQ",
                "minPriceNQ",
                "minPriceHQ",
                "listingsCount",
                "unitsForSale",
            ],
        }

        return params

    async def _fetch_item(self, api_params: dict[str, Any]):
        target_item_id = api_params["item_ids"][0]
        middleware = ItemPriceMiddle(target_item_id, self.item_dict, self.world_dict, self.local_tz)

        raw_data = await MarketClient(self.http_session).get_item_price(**api_params)
        return middleware(raw_data)
