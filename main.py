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
from dcview.submarine.infoboard import AfterSubmarineReturn, InfoBoardView
from itemdict import ItemDict
from itemdict.model import ItemAliasName, ItemCode, ItemName
from submarine.config import ConfigManager
from submarine.enums import Status as SubmarineStatus
from submarine.manager import Manager as SubmarineManager
from submarine.parser import Dumper as SubmarineDumper
from submarine.parser import Loader as SubmarineLoader
from utils.countdown_task import CountdownTaskWrapper
from worker.pricecheck import PriceChecker
from worker.submarine import FollowupMessageWorkerGroup
from worker.submarine_info_board import InfoBoardDisplayer

load_dotenv("test/.env")
GUILDS = [discord.Object(guild) for guild in os.getenv("GUILD", "").split(",")]


class HttpSession:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()


class AraguBot(AraguBotBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.hour_coro_queue: list[Callable[[], Awaitable[None]]] = []

    @loop(hours=1, name="GLOBAL_1H_CLOCK")
    async def global_1h_clock(self):
        for coro in self.hour_coro_queue:
            await coro()

    @global_1h_clock.before_loop
    async def pre_global_1h_clock(self):
        await self.wait_until_ready()

    def create_countdown(self, worker: CountdownTaskWrapper):
        return self.loop.create_task(worker.start())

    def setup_item_dict(self):
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

    def setup_world_dict(self):
        global world_dict
        world_dict = {}
        with open("data/worlds.json", "r", encoding="utf-8") as in_f:
            world_dict = json.load(in_f)

    def setup_local_tz(self):
        global local_tz
        local_tz = pytz.timezone("Asia/Taipei")

    async def setup_submarine(self):
        global local_tz

        global submarine_config
        submarine_config = ConfigManager("submarine/data/config.json", self)
        await submarine_config.fetch_editors()

        global submarine_manager
        loader = SubmarineLoader("submarine/data/state.json", self, local_tz)
        dumper = SubmarineDumper("submarine/data/state.json")
        submarine_manager = SubmarineManager(await loader.load(), dumper, self)

        global sea_zh
        with open("submarine/data/zh.json", "r", encoding="utf-8") as in_f:
            sea_zh = json.load(in_f)

        global submarine_followup_workers
        if submarine_config.announce_channel_id is not None:
            submarine_followup_workers = FollowupMessageWorkerGroup(
                self,
                submarine_manager,
                submarine_config,
            )

    def setup_http_session(self):
        global bot_http_session
        bot_http_session = HttpSession()

    async def reconnect_submarine_infoboard(self):
        global submarine_manager, submarine_config, submarine_followup_workers
        if (
            submarine_config.infoboard_channel_id is None
            or submarine_config.infoboard_message_id is None
        ):
            return

        try:
            infoboard_message = await discord.PartialMessage(
                channel=bot.get_partial_messageable(submarine_config.infoboard_channel_id),
                id=submarine_config.infoboard_message_id,
            ).fetch()
            infoboard = InfoBoardView(
                submarine_manager,
                submarine_config,
                sea_zh,
                local_tz,
                has_submarine_edit_permission,
                submarine_followup_workers,
            )
            infoboard.set_message(infoboard_message)
            await infoboard.update()
            bot.add_view(infoboard, message_id=infoboard_message.id)

            # re-start the timer
            for submarine in submarine_manager.submarines:
                if submarine.status is SubmarineStatus.SAIL:
                    submarine_manager.upsert_timer(
                        submarine,
                        AfterSubmarineReturn(
                            infoboard,
                            submarine,
                            submarine_followup_workers,
                        ).callback,
                    )

            # queue the loop regular update to 1 hour clock
            self.hour_coro_queue.append(infoboard.update)

        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            # reset the config
            submarine_config.infoboard_channel_id = None
            submarine_config.infoboard_message_id = None

    async def setup_hook(self):

        self.setup_item_dict()

        self.setup_world_dict()

        self.setup_local_tz()

        await self.setup_submarine()

        await self.reconnect_submarine_infoboard()

        self.setup_http_session()

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


async def from_others(ctx: commands.Context):
    if bot.user is None:
        return False
    return not ctx.message.author.id == bot.user.id


@commands.check(from_others)
@bot.command(name="ping")
@bot.event
async def ping(ctx: commands.Context):
    return None
    print("pong")
    await ctx.send("pong!")


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


@bot.tree.command(guilds=GUILDS, name="ffxiv-market-buy", description="亞拉戈機械貓 - 繁中市場查價")
async def buy(interaction: discord.Interaction):
    global item_dict, world_dict, bot_http_session, local_tz

    worker = PriceChecker(interaction, item_dict, world_dict, bot_http_session, local_tz)
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


async def has_submarine_edit_permission(interaction_user: discord.User | discord.Member):
    global submarine_config
    whitelist: list[int] = submarine_config.editors
    return await bot.is_owner(interaction_user) or interaction_user.id in whitelist


@bot.tree.command(
    guilds=GUILDS,
    name="ffxiv-company-submarine",
    description="亞拉戈機械貓 - 公會潛水艇",
)
async def connect_submarine_infoboard(interaction: discord.Interaction):
    global submarine_manager, sea_zh, local_tz, submarine_config, submarine_followup_workers

    # for init.
    if (
        submarine_config.infoboard_channel_id is None
        or submarine_config.infoboard_message_id is None
    ):
        # the interaction should never from DM
        assert interaction.channel is not None

        submarine_config.announce_channel_id = interaction.channel.id
        submarine_config.dump()

        submarine_followup_workers = FollowupMessageWorkerGroup(
            bot,
            submarine_manager,
            submarine_config,
        )

        worker = InfoBoardDisplayer(
            interaction,
            submarine_manager,
            submarine_config,
            sea_zh,
            local_tz,
            has_submarine_edit_permission,
            submarine_followup_workers,
        )
        await worker.start()

        assert worker.view is not None
        bot.add_view(worker.view, message_id=submarine_config.infoboard_message_id)

        # queue the loop regular update to 1 hour clock
        bot.hour_coro_queue.append(worker.view.update)

        return

    # in case the user call the command when there is a existing infoboard
    # send them a url jump link
    # there maybe a case that the message is deleted, if true then recreate the infoboard
    try:
        infoboard_message = await discord.PartialMessage(
            channel=bot.get_partial_messageable(submarine_config.infoboard_channel_id),
            id=submarine_config.infoboard_message_id,
        ).fetch()
    except discord.NotFound:
        # in case the message is not exist, create a new message
        worker = InfoBoardDisplayer(
            interaction,
            submarine_manager,
            submarine_config,
            sea_zh,
            local_tz,
            has_submarine_edit_permission,
            submarine_followup_workers,
        )
        await worker.start()

        assert worker.view is not None
        bot.add_view(worker.view, message_id=submarine_config.infoboard_message_id)

        # queue the loop regular update to 1 hour clock
        bot.hour_coro_queue.append(worker.view.update)

        return

    # if the message can be found, send the message url
    infoboard = InfoBoardView(
        submarine_manager,
        submarine_config,
        sea_zh,
        local_tz,
        has_submarine_edit_permission,
        submarine_followup_workers,
    )
    infoboard.set_message(infoboard_message)
    bot.add_view(infoboard, message_id=infoboard_message.id)
    await interaction.response.send_message(
        content=infoboard_message.jump_url,
        ephemeral=True,
    )


bot.run(os.getenv("BOT_TOKEN", ""))
