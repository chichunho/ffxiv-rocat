from typing import Any


class ItemPrice:
    def __init__(self):
        self.pre_soup = {}
        """
        data example with data center provided
        {
        "itemID": 32949,
        "lastUploadTime": 1769816983863,
        "listings": [
            {
            "lastReviewTime": 1769782433,
            "pricePerUnit": 300,
            "quantity": 3,
            "stainID": 0,
            "worldName": "迦樓羅",
            "worldID": 4029,
            "creatorName": "",
            "creatorID": null,
            "hq": false,
            "isCrafted": false,
            "listingID": "283515670341305331",
            "materia": [],
            "onMannequin": false,
            "retainerCity": 7,
            "retainerID": "33777008205319253",
            "retainerName": "肉熊熊",
            "sellerID": null,
            "total": 900,
            "tax": 45
            }
        ],
        "recentHistory": [
            {
            "hq": false,
            "pricePerUnit": 400,
            "quantity": 8,
            "timestamp": 1769788028,
            "onMannequin": false,
            "worldName": "利維坦",
            "worldID": 4030,
            "buyerName": "月風之曲",
            "total": 3200
            }
        ],
        "dcName": "陸行鳥",
        "currentAveragePrice": 966.2923,
        "currentAveragePriceNQ": 966.2923,
        "currentAveragePriceHQ": 0,
        "regularSaleVelocity": 2.7142856,
        "nqSaleVelocity": 2.7142856,
        "hqSaleVelocity": 0,
        "averagePrice": 355.16666,
        "averagePriceNQ": 355.16666,
        "averagePriceHQ": 0,
        "minPrice": 300,
        "minPriceNQ": 300,
        "minPriceHQ": 0,
        "maxPrice": 5000,
        "maxPriceNQ": 5000,
        "maxPriceHQ": 0,
        "stackSizeHistogram": { "1": 15, "2": 20, "3": 21, "4": 4, "5": 2, "10": 2, "50": 1 },
        "stackSizeHistogramNQ": { "1": 15, "2": 20, "3": 21, "4": 4, "5": 2, "10": 2, "50": 1 },
        "stackSizeHistogramHQ": {},
        "worldUploadTimes": {
            "4028": 1769763683305,
            "4029": 1769782436783,
            "4030": 1769799791278,
            "4031": 1769816983863,
            "4032": 1769765349039,
            "4033": 1769763457024,
            "4034": 0,
            "4035": 0
        },
        "listingsCount": 1,
        "recentHistoryCount": 1,
        "unitsForSale": 3,
        "unitsSold": 8,
        "hasData": true
        }
        """

    def __call__(self, raw_data: dict[str, Any]):
        """
        soup structure
        {
            "id": str,
            "update_time": datetime,
            "dc_stats": {
                "hq": {
                    "listings_count": int,
                    "count": int,
                    "avg": float,
                    "min": int
                },
                "nq": {
                    "listings_count": int,
                    "count": int,
                    "avg": float,
                    "min": int
                }
            },
            "world_stats" = {
                "<world>": {
                    "hq": {
                        "listings_count": int,
                        "count": int,
                        "avg": float,
                        "min_per_unit": {
                            "count": int,
                            "total": int,
                            "price": float
                        },
                        "min_total": {
                            "count": int,
                            "total": int,
                        }
                    },
                    "nq": {
                        "listings_count": int,
                        "count": int,
                        "avg": float,
                        "min_per_unit": {
                            "count": int,
                            "total": int,
                            "price": float
                        },
                        "min_total": {
                            "count": int,
                            "price": int,
                        }
                    }
                }
            }
        }
        """

        # get item id
        self.pre_soup["id"] = raw_data["itemID"]

        # get update time
        self.pre_soup["update_time"] = raw_data["lastUploadTime"]

        # get return count
        self.pre_soup["listings_count"] = raw_data["listingsCount"]

        # get dc stats
        self.pre_soup["dc_stats"] = {
            "hq": {
                "listings_count": 0,
                "count": 0,
                "avg": 0,
                "min": 0,
            },
            "nq": {
                "listings_count": 0,
                "count": 0,
                "avg": 0,
                "min": 0,
            },
        }

        if raw_data["minPriceNQ"] > 0:
            self.pre_soup["dc_stats"]["nq"]["avg"] = raw_data["currentAveragePriceNQ"]
            self.pre_soup["dc_stats"]["nq"]["min"] = raw_data["minPriceNQ"]

        if raw_data["minPriceHQ"] > 0:
            self.pre_soup["dc_stats"]["hq"]["avg"] = raw_data["currentAveragePriceHQ"]
            self.pre_soup["dc_stats"]["hq"]["min"] = raw_data["minPriceHQ"]

        # get result
        self.pre_soup["world_stats"] = {}
        for row in raw_data["listings"]:
            if row["worldName"] not in self.pre_soup["world_stats"]:
                self.pre_soup["world_stats"][row["worldName"]] = {
                    "hq": {
                        "listings_count": 0,
                        "count": 0,
                        "total": 0,
                        "avg": 0,
                        "min_per_unit": {
                            "count": 0,
                            "total": 0,
                            "price": 0,
                        },
                        "min_total": {
                            "count": 0,
                            "price": 0,
                            "quantity": 0,
                        },
                    },
                    "nq": {
                        "listings_count": 0,
                        "count": 0,
                        "total": 0,
                        "avg": 0,
                        "min_per_unit": {
                            "count": 0,
                            "total": 0,
                            "price": 0,
                        },
                        "min_total": {
                            "count": 0,
                            "price": 0,
                            "quantity": 0,
                        },
                    },
                }

            if row["hq"]:
                entry_ptr = self.pre_soup["world_stats"][row["worldName"]]["hq"]
                self.pre_soup["dc_stats"]["hq"]["listings_count"] += 1
                self.pre_soup["dc_stats"]["hq"]["count"] += row["quantity"]
            else:
                entry_ptr = self.pre_soup["world_stats"][row["worldName"]]["nq"]
                self.pre_soup["dc_stats"]["nq"]["listings_count"] += 1
                self.pre_soup["dc_stats"]["nq"]["count"] += row["quantity"]

            entry_ptr["listings_count"] += 1

            entry_ptr["count"] += row["quantity"]

            entry_ptr["total"] += row["total"]

            if (
                entry_ptr["min_per_unit"]["count"] == 0
                or entry_ptr["min_per_unit"]["price"] > row["pricePerUnit"]
            ):
                entry_ptr["min_per_unit"]["price"] = row["pricePerUnit"]
                entry_ptr["min_per_unit"]["count"] = 1
                entry_ptr["min_per_unit"]["total"] = row["total"]
            elif entry_ptr["min_per_unit"]["price"] == row["pricePerUnit"]:
                entry_ptr["min_per_unit"]["count"] += 1

            if (
                entry_ptr["min_total"]["count"] == 0
                or entry_ptr["min_total"]["price"] > row["total"]
            ):
                entry_ptr["min_total"]["price"] = row["total"]
                entry_ptr["min_total"]["count"] = 1
            elif entry_ptr["min_total"]["price"] == row["total"]:
                entry_ptr["min_total"]["count"] += 1

        for world in self.pre_soup["world_stats"].values():
            if world["hq"]["count"] > 0:
                world["hq"]["avg"] = float(world["hq"]["total"]) / world["hq"]["count"]
            if world["nq"]["count"] > 0:
                world["nq"]["avg"] = float(world["nq"]["total"]) / world["nq"]["count"]

        return self.pre_soup
