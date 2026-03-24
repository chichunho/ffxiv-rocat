import json
from datetime import datetime
from typing import Any

from discord import Forbidden, HTTPException, NotFound
from pytz import BaseTzInfo

from submarine.enums import Sea, Status
from submarine.model import FollowupMessage, OperatorInfo, SailInfo, Submarine
from utils.cache import DiscordGuildCache


class Loader:
    def __init__(
        self,
        fp: str,
        guild_cache: DiscordGuildCache,
        local_tz: BaseTzInfo,
    ):
        self.fp = fp
        self.guild_cache = guild_cache
        self.local_tz = local_tz

        self.cache: list[dict[str, Any]] | None = None
        self.refresh()

    def refresh(self):
        with open(self.fp, "r", encoding="utf-8") as in_f:
            self.cache = json.load(in_f)

    async def load(self) -> list[Submarine]:
        res: list[Submarine] = []

        assert self.cache is not None
        for state in self.cache:
            # submrine name
            name = state["name"]

            # submarine status
            status = Status(state["status"])

            # submarine operator
            _operator_info = state["operator_info"]
            # if the submarine is idle then there will be no op info
            # or if the state format is wrong
            if status is Status.IDLE or len(_operator_info) != 2:
                operator_info = None
            else:
                try:
                    operator = await self.guild_cache.get_member(
                        _operator_info["operator"]["id"]
                    )
                    editor = (
                        None
                        if _operator_info["editor"] is None
                        else await self.guild_cache.get_member(
                            _operator_info["editor"]["id"]
                        )
                    )
                except (NotFound, HTTPException, Forbidden) as e:
                    print(e)
                    operator_info = None
                    continue

                operator_info = OperatorInfo(operator, editor)

            # submarine sail info
            _sail_info = state["sail_info"]
            # if the submarine is idle then there will be no sail info
            # or if the state format is wrong
            if status is Status.IDLE or len(_sail_info) != 3:
                sail_info = None
            else:
                sea = Sea(_sail_info["sea"])
                route = _sail_info["route"]
                end_dt = self.local_tz.localize(
                    datetime.fromtimestamp(_sail_info["return_dt"])
                )

                sail_info = SailInfo(sea, route, end_dt)

            note = state["note"]

            _followup_message = state["followup_message"]
            followup_message = None
            if status is Status.RETURNED:
                followup_message = FollowupMessage(
                    _followup_message["channel_id"], _followup_message["message_id"]
                )

            res.append(
                Submarine(
                    name,
                    status,
                    operator_info,
                    sail_info,
                    note,
                    followup_message,
                )
            )

        return res


class Dumper:
    def __init__(self, fp: str):
        self.fp = fp

    def dump(self, ss: list[Submarine]):
        res = []
        for s in ss:
            _op_info: dict[str, Any] | None
            _sail_info: dict[str, Any] | None

            if s.status is Status.IDLE:
                _op_info = None
                _sail_info = None
            else:
                assert s.operator_info is not None
                assert s.sail_info is not None

                _op_info = {
                    "operator": {
                        "id": s.operator_info.operator.id,
                        "name": s.operator_info.operator.display_name,
                    },
                    "editor": None
                    if s.operator_info.editor is None
                    else {
                        "id": s.operator_info.editor.id,
                        "name": s.operator_info.editor.display_name,
                    },
                }
                _sail_info = {
                    "sea": s.sail_info.sea.value,
                    "route": s.sail_info.route,
                    "return_dt": int(s.sail_info.return_dt.timestamp()),
                }

            _followup_message: dict[str, Any] | None
            if s.status is Status.RETURNED:
                assert s.followup_message is not None
                _followup_message = {
                    "channel_id": s.followup_message.channel_id,
                    "message_id": s.followup_message.message_id,
                }
            else:
                _followup_message = None

            _d = {
                "name": s.name,
                "status": s.status.value,
                "operator_info": _op_info,
                "sail_info": _sail_info,
                "note": s.note,
                "followup_message": _followup_message,
            }

            res.append(_d)

        with open(self.fp, "w", encoding="utf-8") as out_f:
            json.dump(res, out_f, ensure_ascii=False)
