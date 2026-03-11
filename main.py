import json
import os

import aiohttp
import discord
import pytz
from discord.ext import commands
from dotenv import load_dotenv

from market.itemdict import ItemDict
from worker.pricechecker import PriceChecker

load_dotenv("test/.env")
TEST_GUILD = discord.Object(670441933931413514)


class HttpSession:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()


class AraguBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def setup_hook(self):
        global item_dict
        with open("market/data/item_pinyin.json", "r", encoding="utf-8") as in_f:
            fuzzy_dict: dict[str, list[str]] = json.load(in_f)
        with open("market/data/item.json", "r", encoding="utf-8") as in_f:
            default_dict: dict[str, str] = json.load(in_f)
        with open("market/data/item_hotfix.json", "r", encoding="utf-8") as in_f:
            hotfix_dict: dict[str, str] = json.load(in_f)
        with open("market/data/item_alias.json") as in_f:
            alias_dict: dict[str, str] = json.load(in_f)
        with open("market/data/item_cn.json", "r", encoding="utf-8") as in_f:
            sc_dict: dict[str, str] = json.load(in_f)

        item_dict = ItemDict(
            default_dict | hotfix_dict,
            alias_dict,
            fuzzy_dict,
            sc_dict,
        )

        global world_dict
        world_dict = {}
        with open("data/worlds.json", "r", encoding="utf-8") as in_f:
            world_dict = json.load(in_f)

        global local_tz
        local_tz = pytz.timezone("Asia/Taipei")

        global bot_http_session
        bot_http_session = HttpSession()

        # self.tree.clear_commands(guild=None)
        # await self.tree.sync()
        # self.tree.clear_commands(guild=TEST_GUILD)
        await self.tree.sync(guild=TEST_GUILD)

    async def close(self):
        global bot_http_session
        await bot_http_session.close()
        await super().close()


intents = discord.Intents.default()
intents.message_content = True

bot = AraguBot(command_prefix=commands.when_mentioned_or("$"), intents=intents)


async def from_others(ctx: commands.Context):
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


@bot.tree.command(
    guild=TEST_GUILD, name="ffxiv-market-buy", description="亞拉戈機械貓 - 繁中市場查價"
)
async def buy(interaction: discord.Interaction):
    global item_dict, world_dict, bot_http_session, local_tz

    worker = PriceChecker(
        interaction, item_dict, world_dict, bot_http_session, local_tz
    )
    await worker.start()


bot.run(os.getenv("BOT_TOKEN"))
