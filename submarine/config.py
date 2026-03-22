import json
from typing import Any

import discord

from base import AraguBotBase


class ConfigManager:
    def __init__(self, fp: str, bot: AraguBotBase):
        self.fp = fp
        self.bot = bot
        self.fetched_editors: list[discord.User | discord.Member] = []
        self.content: dict[str, Any] = {}
        self.load()

    def load(self):
        with open(self.fp, "r", encoding="utf-8") as in_f:
            self.content = json.load(in_f)

    def dump(self):
        with open(self.fp, "w", encoding="utf-8") as out_f:
            json.dump(self.content, out_f, ensure_ascii=False)

    async def fetch_editors(self):
        for uid in self.content["editors"]:
            try:
                self.fetched_editors.append(await self.bot.fetch_user(uid))
            except (discord.NotFound, discord.HTTPException):
                continue

    @property
    def infoboard_channel_id(self):
        return self.content["infoboard"]["channel_id"]

    @infoboard_channel_id.setter
    def infoboard_channel_id(self, cid: int | None):
        self.content["infoboard"]["channel_id"] = cid

    @property
    def infoboard_message_id(self):
        return self.content["infoboard"]["message_id"]

    @infoboard_message_id.setter
    def infoboard_message_id(self, cid: int | None):
        self.content["infoboard"]["message_id"] = cid

    @property
    def announce_channel_id(self):
        return self.content["announce_channel_id"]

    @announce_channel_id.setter
    def announce_channel_id(self, cid: int | None):
        self.content["announce_channel_id"] = cid

    @property
    def editors(self):
        return self.content["editors"]

    @editors.setter
    def editors(self, uids: list[int]):
        self.content["editors"] = uids

    @property
    def note_template(self):
        return self.content["note_template"]

    @note_template.setter
    def note_template(self, x: str):
        self.content["note_template"] = x
