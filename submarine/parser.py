import json
from datetime import datetime, tzinfo
from typing import Any

from base import AraguBotBase
from submarine.enums import Sea, Status
from submarine.model import OperatorInfo, SailInfo, Submarine


class Loader:
    """sr struct example
    [
        {
            "name": "s1"
            "status": "SAIL"
            "operator_info": {
                "operator": {
                    "id": 386528364,
                    "name": "test 1",
                },
                "editor": null,
            }
            "sail_info": {
                "sea": "DEEP",
                "route": ["A", "B", "E"],
                "end_dt": 1773801778,
            }
        },
        ...
    ]
    """

    def __init__(self, fp: str, bot: AraguBotBase, local_tz: tzinfo):
        self.fp = fp
        self.bot = bot
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
                operator = await self.bot.fetch_user(_operator_info["operator"]["id"])
                editor = (
                    None
                    if _operator_info["editor"] is None
                    else await self.bot.fetch_user(_operator_info["editor"]["id"])
                )

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
                end_dt = datetime.fromtimestamp(_sail_info["return_dt"]).astimezone(self.local_tz)

                sail_info = SailInfo(sea, route, end_dt)

            note = state["note"]

            followup_message_id = state["followup_message_id"]

            res.append(Submarine(name, status, operator_info, sail_info, note, followup_message_id))

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
                    "return_dt": s.sail_info.return_dt.timestamp(),
                }

            _d = {
                "name": s.name,
                "status": s.status.value,
                "operator_info": _op_info,
                "sail_info": _sail_info,
                "note": s.note,
                "followup_message_id": s.followup_message_id,
            }

            res.append(_d)

        with open(self.fp, "w", encoding="utf-8") as out_f:
            json.dump(res, out_f, ensure_ascii=False)
