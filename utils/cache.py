from collections.abc import Iterable
from typing import Any

import discord


class CachedMember(discord.Member):
    def __hash__(self):
        return self.id

    def __eq__(self, x: Any):
        return isinstance(x, (discord.Member, CachedMember)) and self.id == x.id


class DiscordGuildCache:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self._cached_members: dict[int, discord.Member] = {}

    def refresh(self): ...

    async def get_member(self, user_id: int) -> discord.Member:
        try:
            return self._cached_members[user_id]
        except KeyError:
            pass

        new_member = await self.guild.fetch_member(user_id)
        self._cached_members[new_member.id] = new_member

        return new_member

    async def get_memebers(self, uids: Iterable[int]) -> list[discord.Member]:
        res = []
        for uid in uids:
            try:
                res.append(await self.get_member(uid))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                res.append(None)
        return res
