from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable

import aiohttp
import discord
import pytz
from discord.ext import commands
from discord.ext.tasks import loop
from dotenv import load_dotenv

from base import AraguBotBase
from itemdict import ItemDict
from itemdict.model import ItemAliasName, ItemCode, ItemName
from submarine.config import ConfigManager as SubmarineConfigManager
from submarine.manager import SubmarineManager
from submarine.parser import Dumper as SubmarineDumper
from submarine.parser import Loader as SubmarineLoader
from submarine.seadict import SeaDict
from utils.cache import DiscordGuildCache
from utils.countdown_task import CountdownTaskWrapper
from worker.pricecheck import PriceChecker
from worker.submarine import FollowupMessageWorkerGroup
from worker.submarine_info_board import InfoBoardDisplayer

load_dotenv("test/.env")
GUILDS = [discord.Object(guild) for guild in os.getenv("GUILD", "").split(",")]


####################################################################################################
# BEGIN of class
####################################################################################################


class HttpSession:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()


####################################################################################################
# END of class
####################################################################################################


####################################################################################################
# BEGIN of global var
####################################################################################################

# general
local_tz: pytz.BaseTzInfo
bot_http_session: HttpSession

# market
item_dict: ItemDict
world_dict: dict[str, str]

# submarine
submarine_config: SubmarineConfigManager
submarine_followup_workers: FollowupMessageWorkerGroup
submarine_guild_cache: (
    DiscordGuildCache | None
)  # if init then no guild id -> no guild cache
sea_zh: SeaDict

####################################################################################################
#  BEGIN of setup_hook methods
####################################################################################################


def setup_item_dict():
    global item_dict
    with open("market/data/item_pinyin.json", "r", encoding="utf-8") as in_f:
        fuzzy_dict: dict[str, list[ItemCode]] = json.load(in_f)

    with open("market/data/item.json", "r", encoding="utf-8") as in_f:
        default_dict: dict[ItemCode, ItemName] = json.load(in_f)

    with open("market/data/item_hotfix.json", "r", encoding="utf-8") as in_f:
        hotfix_dict: dict[ItemCode, ItemName] = json.load(in_f)

    with open("market/data/item_alias.json") as in_f:
        alias_dict: dict[ItemAliasName, ItemCode] = json.load(in_f)

    with open("market/data/item_cn.json", "r", encoding="utf-8") as in_f:
        sc_dict: dict[ItemCode, ItemName] = json.load(in_f)

    item_dict = ItemDict(
        default_dict | hotfix_dict,
        alias_dict,
        fuzzy_dict,
        sc_dict,
    )


def setup_world_dict():
    global world_dict
    world_dict = {}
    with open("data/worlds.json", "r", encoding="utf-8") as in_f:
        world_dict = json.load(in_f)


def setup_local_tz():
    global local_tz
    local_tz = pytz.timezone("Asia/Taipei")


def setup_http_session():
    global bot_http_session
    bot_http_session = HttpSession()


async def setup_submarine(bot: AraguBotBase):

    # steps
    # 1. load config.json
    #   1.1 for init, no submarine data, no guild id, no infoboard, defer to the begin of command
    #     1.1.1 skip reconnect infoboard
    #     1.1.2 skip loader
    # 2. load submarine state dumper
    # 3. load guild cache for ui display name
    #   3.1 for init, no guild id, defer to begin of command
    # 4. load sea zh names
    # 5. init submarine followup message work group
    #   5.1 for init, no announce channel id, defer to begin of command

    global local_tz

    global submarine_config
    submarine_config = SubmarineConfigManager("submarine/data/config.json")

    dumper = SubmarineDumper("submarine/data/state.json")

    global submarine_manager
    submarine_manager = SubmarineManager(bot, dumper)

    global sea_zh
    with open("submarine/data/sea.json", "r", encoding="utf-8") as in_f:
        sea_zh = SeaDict(json.load(in_f))

    global submarine_guild_cache
    submarine_guild_cache = None

    global submarine_followup_workers
    submarine_followup_workers = FollowupMessageWorkerGroup(
        bot,
        submarine_config,
    )

    if (
        submarine_config.guild_id is not None
        and submarine_config.announce_channel_id is not None
    ):
        submarine_guild_cache = DiscordGuildCache(
            await bot.fetch_guild(submarine_config.guild_id)
        )

        loader = SubmarineLoader(
            "submarine/data/state.json",
            submarine_guild_cache,
            local_tz,
        )

        for submarine in await loader.load():
            submarine_manager.manage(submarine)


####################################################################################################
#  END of setup_hooks methods
####################################################################################################


####################################################################################################
# START of bot
####################################################################################################


class AraguBot(AraguBotBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.hour_coro_queue: dict[str, Callable[[], Awaitable[None]]] = {}
        self.queue_lock = asyncio.Lock()

    async def upsert_scheduled_job(
        self, job_id: str, coro: Callable[[], Awaitable[None]]
    ):
        async with self.queue_lock:
            self.hour_coro_queue[job_id] = coro

    async def cancel_schedule_job(self, job_id: str):
        async with self.queue_lock:
            del self.hour_coro_queue[job_id]

    @loop(hours=1, name="GLOBAL_1H_CLOCK")
    async def global_1h_clock(self):
        async with self.queue_lock:
            for coro in self.hour_coro_queue.values():
                await coro()

    @global_1h_clock.before_loop
    async def pre_global_1h_clock(self):
        await self.wait_until_ready()

    def create_countdown(self, worker: CountdownTaskWrapper):
        return self.loop.create_task(worker.start())

    async def setup_hook(self):

        setup_item_dict()

        setup_world_dict()

        setup_local_tz()

        await setup_submarine(self)

        setup_http_session()

        self.global_1h_clock.start()

        # self.tree.clear_commands(guild=None)
        # await self.tree.sync()
        # self.tree.clear_commands(guild=TEST_GUILD)
        for guild in GUILDS:
            await self.tree.sync(guild=guild)

    async def close(self):
        global bot_http_session
        self.global_1h_clock.cancel()
        await bot_http_session.close()
        await super().close()


intents = discord.Intents.default()
intents.message_content = True

bot = AraguBot(command_prefix=commands.when_mentioned_or("$"), intents=intents)


####################################################################################################
# END of bot
####################################################################################################


####################################################################################################
# BEGIN OF on_ready methods
####################################################################################################

...

####################################################################################################
# END of on_ready methods
####################################################################################################


####################################################################################################
# BEGIN of on_ready
####################################################################################################


@bot.event
async def on_ready():
    global \
        bot, \
        submarine_manager, \
        submarine_config, \
        submarine_followup_workers, \
        submarines, \
        submarine_guild_cache

    await InfoBoardDisplayer.reconnect(
        bot,
        submarine_manager,
        submarine_config,
        sea_zh,
        local_tz,
        has_submarine_edit_permission,
        submarine_followup_workers,
        submarine_guild_cache,
    )


####################################################################################################
# END of on_ready
####################################################################################################


####################################################################################################
#  BEGIN of checks
####################################################################################################


async def from_others(ctx: commands.Context):
    if bot.user is None:
        return False
    return not ctx.message.author.id == bot.user.id


async def from_owner(ctx: commands.Context):
    if bot.user is None:
        return False
    return await bot.is_owner(ctx.message.author)


async def has_submarine_edit_permission(
    interaction_user: discord.User | discord.Member,
):
    global submarine_config
    whitelist: set[int] = submarine_config.editor_ids
    return await bot.is_owner(interaction_user) or interaction_user.id in whitelist


####################################################################################################
#  END of checks
####################################################################################################


####################################################################################################
# BEGIN of commands
####################################################################################################


@commands.check(from_owner)
@commands.check(from_others)
@bot.command(name="rm")
@bot.event
async def rm(ctx: commands.Context, message_id):
    try:
        target_msg = await ctx.fetch_message(int(message_id))
    except (discord.NotFound, discord.Forbidden):
        return

    await target_msg.delete()


@commands.check(from_others)
@bot.command(name="alias")
@bot.event
async def alias(ctx: commands.Context, item_name, item_nickname):
    return
    # global item_dict, item_alias

    # if item_name not in item_dict:
    #     await ctx.send(f"{item_name} is not found")

    # if item_nickname not in item_dict:
    #     item_alias[item_nickname] = item_dict[item_name]
    #     item_dict[item_nickname] = item_dict[item_name]
    #     with open("item_alias.json", "w", encoding="utf-8") as out_f:
    #         json.dump(item_alias, out_f)
    #     await ctx.send(f"{item_nickname} is now an alias of item {item_name}")
    # else:
    #     await ctx.send(f"{item_nickname} is an alias of item {item_dict[item_nickname]}")


@bot.tree.command(
    guilds=GUILDS, name="ffxiv-market-buy", description="亞拉戈機械貓 - 繁中市場查價"
)
async def buy(interaction: discord.Interaction):
    global item_dict, world_dict, bot_http_session, local_tz

    worker = PriceChecker(
        interaction, item_dict, world_dict, bot_http_session, local_tz
    )
    await worker.start()


# TODO: implement
# @bot.tree.command(
#     guilds=GUILDS,
#     name="ffxiv-market-alias",
#     description="亞拉戈機械貓 - 市場物品別名",
# )
# async def add_alias(interaction: discord.Interaction):
#     global item_dict, world_dict, bot_http_session, local_tz

#     worker = AliasPanel(interaction, item_dict, world_dict, bot_http_session, local_tz)
#     await worker.start()


@bot.tree.command(
    guilds=GUILDS,
    name="ffxiv-company-submarine",
    description="亞拉戈機械貓 - 公會潛水艇",
)
async def connect_submarine_infoboard(interaction: discord.Interaction):
    global \
        bot, \
        submarine_manager, \
        sea_zh, \
        local_tz, \
        submarine_config, \
        submarine_followup_workers, \
        submarine_guild_cache, \
        submarine_guild_cache

    worker = InfoBoardDisplayer(
        bot,
        interaction,
        submarine_config,
        submarine_manager,
        sea_zh,
        local_tz,
        has_submarine_edit_permission,
        submarine_followup_workers,
        submarine_guild_cache,
    )

    await worker.start()


bot.run(os.getenv("BOT_TOKEN", ""))
