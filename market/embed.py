from typing import Any

from discord import Embed


class ItemPriceEmbed:
    def __init__(self, soup: dict[str, Any]):
        self.soup = soup

    def message(self):
        title = f"物品名稱: {self.soup['name']}"
        description = "\n".join(
            [
                "艾奧傑亞",
                "```",
                f"{'NQ':>19}{'HQ':>12}",
                f"市場列數{self.soup['dc_stats']['nq']['listings_count']:>12}{self.soup['dc_stats']['hq']['listings_count']:>12}",
                f"物品個數{self.soup['dc_stats']['nq']['count']:>12}{self.soup['dc_stats']['hq']['count']:>12}",
                # f"平均售價{self.soup['dc_stats']['nq']['avg']:>12}{self.soup['dc_stats']['hq']['avg']:>12}",
                f"最低售價{self.soup['dc_stats']['nq']['min']:>12,}{self.soup['dc_stats']['hq']['min']:>12,}",
                "```",
            ]
        )

        embed = Embed(title=title, description=description)

        for world_name, world_stat in self.soup["world_stats"].items():
            field_value = "\n".join(
                [
                    "```",
                    f"{'NQ':>14}{'HQ':>15}",
                    f"市場列數{world_stat['nq']['listings_count']:>7}{world_stat['hq']['listings_count']:>15}",
                    f"物品個數{world_stat['nq']['count']:>7}{world_stat['hq']['count']:>15}",
                    "\n",
                    "每件",
                    f"最低{world_stat['nq']['min_per_unit']['price']:>10,}{'(' + str(world_stat['nq']['min_per_unit']['count']) + ')':<5}{world_stat['hq']['min_per_unit']['price']:>10,}({world_stat['hq']['min_per_unit']['count']})",
                    "\n",
                    "每列",
                    f"最低{world_stat['nq']['min_total']['price']:>10,}{'(' + str(world_stat['nq']['min_total']['count']) + ')':<5}{world_stat['hq']['min_total']['price']:>10,}({world_stat['hq']['min_total']['count']})",
                    "```",
                ]
            )
            embed = embed.add_field(
                name=world_name,
                value=field_value,
                inline=False,
            )

        embed.set_footer(text=f"資料更新於 {self.soup['update_time']}")

        return embed
