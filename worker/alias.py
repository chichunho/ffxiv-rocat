from datetime import tzinfo
from typing import Any

import discord

from dcview.alias.add import AddAliasView
from dcview.alias.enums import PanelOption
from dcview.alias.panel import PanelView
from dcview.alias.search import ItemSearchView
from dcview.alias.validate import ContinueView, FailView, ValidateView
from itemdict import ItemDict
from itemdict.enums import DictScope
from itemdict.model import Item
from market.enums import AdvancedSearchOption
from market.search import ItemKeyword
from worker.worker import Worker


class AliasValidator(Worker):
    def __init__(self, interaction: discord.Interaction, item_dict: ItemDict):
        self.interaction = interaction
        self.item_dict = item_dict

    async def start(self):
        val_modal = ValidateView()
        await self.interaction.response.send_modal(val_modal)
        is_timeout = await val_modal.wait()
        self.interaction.delete_original_response()
        if is_timeout:
            return

        if self.item_dict.contains(val_modal.new_alias, DictScope.ALIAS):
            await self.interaction.followup.send(view=FailView(), ephemeral=True)
            return

        continue_view = ContinueView()
        msg = await self.interaction.followup.send(
            view=continue_view,
            ephemeral=True,
            wait=True,
        )

        is_timeout = await continue_view.wait()
        if is_timeout:
            await msg.delete()

        next_worker = AliasAdder(
            val_modal.new_alias,
            continue_view.next_interaction,
            self.item_dict,
        )

        await next_worker.start()


class AliasAdder(Worker):
    def __init__(
        self,
        alias_name: str,
        interaction: discord.Interaction,
        item_dict: ItemDict,
    ):
        self.alias_name = alias_name
        self.interaction = interaction
        self.item_dict = item_dict

    async def start(self):
        item_modal = ItemSearchView()
        await self.interaction.response.send_modal(item_modal)

        is_timeout = await item_modal.wait()
        if is_timeout:
            return

        keyword = ItemKeyword(
            item_modal.master_keyword,
            item_modal.filter_keyword,
        )

        # there may be no filter in initial, but new in processed keyword
        check_options = item_modal.search_options
        if len(keyword.filter_words) > 0:
            check_options.add(AdvancedSearchOption.OPT_CONTAINS)

        items: list[Item] = []
        items = self.item_dict.search(
            keyword,
            check_options=check_options,
            case_insensitive=(AdvancedSearchOption.OPT_CASE_INSENSITIVE in check_options),
        )

        add_alias_view = AddAliasView(items)
        msg = await self.interaction.followup.send(view=add_alias_view, wait=True)
        is_timeout = await add_alias_view.wait()
        await msg.delete()
        if is_timeout:
            return

        self.item_dict.add_alias(
            self.item_dict.encode(add_alias_view.dropdown.value),
            self.alias_name,
        )


class PanelDisplayer(Worker):
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
        # user select the alias ops
        menu_view = PanelView(self.item_dict)
        await self.interaction.response.send_message(view=menu_view, ephemeral=True)
        await menu_view.wait()
        await self.interaction.delete_original_response()
        if menu_view.option is None:
            return

        next_worker: Worker
        match menu_view.option:
            case PanelOption.ADD:
                next_worker = AliasValidator(menu_view.next_interaction, self.item_dict)
            case PanelOption.DELETE:
                pass
            case PanelOption.UPDATE:
                pass

        await next_worker.start()
