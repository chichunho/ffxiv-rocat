from typing import Any

import discord
from dcview.buy.dropdown import InfoButton


class ReportHeader(discord.ui.TextDisplay):
    def __init__(self, content: str):
        super().__init__(content=f"# 物品名稱: {content}")


class EozeaReport(discord.ui.Container):
    def __init__(self, soup: dict[str, Any]):
        super().__init__()

        self.title = "## 艾奧傑亞"
        self.text = "\n".join(
            [
                "```",
                f"{'NQ':>19}{'HQ':>12}",
                f"市場列數{soup['dc_stats']['nq']['listings_count']:>12}{soup['dc_stats']['hq']['listings_count']:>12}",
                f"物品個數{soup['dc_stats']['nq']['count']:>12}{soup['dc_stats']['hq']['count']:>12}",
                # f"平均售價{self.soup['dc_stats']['nq']['avg']:>12}{self.soup['dc_stats']['hq']['avg']:>12}",
                f"最低售價{soup['dc_stats']['nq']['min']:>12,}{soup['dc_stats']['hq']['min']:>12,}",
                "```",
            ]
        )

        self.add_item(discord.ui.TextDisplay(content=self.title))
        self.add_item(discord.ui.TextDisplay(content=self.text))


class WorldReport(discord.ui.Container):
    def __init__(self, world: str, stat: dict[str, Any]):
        super().__init__()

        self.title = f"## {world}"
        self.text = "\n".join(
            [
                "```",
                f"{'NQ':>14}{'HQ':>15}",
                f"市場列數{stat['nq']['listings_count']:>7}{stat['hq']['listings_count']:>15}",
                f"物品個數{stat['nq']['count']:>7}{stat['hq']['count']:>15}",
                "\n",
                "每件",
                f"最低{stat['nq']['min_per_unit']['price']:>10,}{'(' + str(stat['nq']['min_per_unit']['count']) + ')':<5}{stat['hq']['min_per_unit']['price']:>10,}({stat['hq']['min_per_unit']['count']})",
                "\n",
                "每列",
                f"最低{stat['nq']['min_total']['price']:>10,}{'(' + str(stat['nq']['min_total']['count']) + ')':<5}{stat['hq']['min_total']['price']:>10,}({stat['hq']['min_total']['count']})",
                "```",
            ]
        )

        self.add_item(discord.ui.TextDisplay(content=self.title))
        self.add_item(discord.ui.TextDisplay(content=self.text))


class ReportFooter(discord.ui.TextDisplay):
    def __init__(self, content: str):
        super().__init__(content=f"-# 資料更新於 {content}")


class PriceResultView(discord.ui.LayoutView):
    def __init__(self, soup: dict[str, Any], inherited_info_btn: InfoButton):
        super().__init__()

        self.add_item(ReportHeader(soup["name"]))
        self.add_item(discord.ui.ActionRow(inherited_info_btn))
        self.add_item(EozeaReport(soup))
        for world_name, world_stat in soup["world_stats"].items():
            self.add_item(WorldReport(world_name, world_stat))
        self.add_item(ReportFooter(soup["update_time"]))
