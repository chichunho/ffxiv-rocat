import json
from collections.abc import Iterable
from typing import Any

import discord


class ConfigManager:
    def __init__(self, fp: str):
        self.fp = fp
        self.content: dict[str, Any] = {}
        self.load()

        # for optimization
        self._editor_ids_set: set[int] | None = None

        # for api call optimization
        # maintain a discord.Member cache
        self._cached_fetched_editors: set[discord.Member] = set()

    def load(self):
        with open(self.fp, "r", encoding="utf-8") as in_f:
            self.content = json.load(in_f)

    def dump(self):
        with open(self.fp, "w", encoding="utf-8") as out_f:
            _d = {
                "infoboard": {
                    "channel_id": self.infoboard_channel_id,
                    "message_id": self.infoboard_message_id,
                },
                "guild_id": self.guild_id,
                "announce_channel_id": self.announce_channel_id,
                "editor_ids": list(self.editor_ids),
                "note_template": self.note_template,
            }
            json.dump(_d, out_f, ensure_ascii=False)

    @property
    def infoboard_channel_id(self) -> int | None:
        return self.content["infoboard"]["channel_id"]

    @infoboard_channel_id.setter
    def infoboard_channel_id(self, cid: int | None):
        self.content["infoboard"]["channel_id"] = cid

    @property
    def infoboard_message_id(self) -> int | None:
        return self.content["infoboard"]["message_id"]

    @infoboard_message_id.setter
    def infoboard_message_id(self, cid: int | None):
        self.content["infoboard"]["message_id"] = cid

    @property
    def announce_channel_id(self) -> int | None:
        return self.content["announce_channel_id"]

    @announce_channel_id.setter
    def announce_channel_id(self, cid: int | None):
        self.content["announce_channel_id"] = cid

    @property
    def editor_ids(self) -> set[int]:
        if self._editor_ids_set is None:
            self._editor_ids_set = set(self.content["editor_ids"])
        return self._editor_ids_set

    @editor_ids.setter
    def editor_ids(self, uids: Iterable[int]):
        self._editor_ids_set = set(uids)

    @property
    def note_template(self) -> str:
        return self.content["note_template"]

    @note_template.setter
    def note_template(self, x: str):
        self.content["note_template"] = x

    @property
    def guild_id(self) -> int | None:
        return self.content["guild_id"]

    @guild_id.setter
    def guild_id(self, x: int | None):
        self.content["guild_id"] = x
