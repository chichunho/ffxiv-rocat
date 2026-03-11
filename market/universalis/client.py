from datetime import datetime, timedelta
from typing import Any


class Client:
    def __init__(self, session):
        self.session = session.session
        self.host = "https://universalis.app"

    async def get_data_centers(self):
        endpoint = "/api/v2/data-centers"

        async with self.session.get(url=f"{self.host}{endpoint}") as response:
            if response.status == 200:
                return await response.json()

        return None

    async def get_worlds(self):
        endpoint = "/api/v2/worlds"

        async with self.session.get(url=f"{self.host}{endpoint}") as response:
            if response.status == 200:
                return await response.json()

        return None

    async def get_item_price_agg(
        self,
        item_ids: list[int],
        location: str | int,
    ):
        endpoint = f"/api/v2/aggregated/{location}/{','.join([str(s) for s in item_ids])}"

        async with self.session.get(url=f"{self.host}{endpoint}") as response:
            if response.status == 200:
                return await response.json()

        return None

    async def get_item_price(
        self,
        item_ids: list[int],
        location: str | int,
        hq: bool | None = None,
        listings: int | None = None,
        sale_entries: int | None = None,
        stats_within: timedelta | None = None,
        sale_entries_within: timedelta | None = None,
        fields: list[str] | None = None,
    ):
        endpoint = f"/api/v2/{location}/{','.join([str(s) for s in item_ids])}"

        params = {
            "hq": hq,
            "listings": listings,
            "entries": sale_entries,
            "statsWithin": (stats_within.microseconds * 1000 if stats_within is not None else None),
            "entriesWithin": (
                sale_entries_within.seconds if sale_entries_within is not None else None
            ),
            "fields": ",".join(fields),
        }

        async with self.session.get(
            url=f"{self.host}{endpoint}",
            params=Client._filter_None(params),
        ) as response:
            if response.status == 200:
                return await response.json()

        return None

    async def get_sale_history(
        self,
        item_ids: list[int],
        location: str | int,
        n: int | None = None,
        stats_within: timedelta | None = None,
        entries_within: timedelta | None = None,
        entries_until: datetime | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
    ):
        endpoint = f"/api/v2/history/{location}/{','.join([str(s) for s in item_ids])}"

        params = {
            "entriesToReturn": n,
            "statsWithin": stats_within.microseconds * 1000,
            "entriesWithin": entries_within.seconds,
            "entriesUntil": entries_until.timestamp(),
            "minSalePrice": min_price,
            "maxSalePrice": max_price,
        }

        async with self.session.get(
            url=f"{self.host}{endpoint}",
            params=params,
        ) as response:
            if response.status == 200:
                return await response.json()

        return None

    async def get_updated_items(
        self,
        world: str | int,
        data_center: str,
        n: int,
    ):
        endpoint = "/api/v2/extra/stats/most-recently-updated"

        params = {
            "entries": n,
        }

        async with self.session.get(
            url=f"{self.host}{endpoint}",
            params=params,
        ) as response:
            if response.status == 200:
                return await response.json()

        return None

    def _filter_None(params: dict[str, Any]):
        return {k: v for k, v in params.items() if v is not None}
