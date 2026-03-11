import discord

from market.itemdict import AdvancedSearchOption
from dcview.enums import ReplyOption
from dcview.protocol import ItemSearchForm


class ItemSearchView(discord.ui.Modal, ItemSearchForm):
    def __init__(self, title: str):
        super().__init__(title=title, timeout=180)

    _master_keyword = discord.ui.Label(
        text="物品關鍵字",
        description="物品編號, 正體中文字詞, 拚音首字母, 萬用字符(*)\n例如: 納夏鞣革, 納夏, nxrg, 納**g",
        component=discord.ui.TextInput(
            placeholder="",
        ),
    )

    _filter_keyword = discord.ui.Label(
        text="包含字詞",
        description="物品必包含以上字詞, 如有多個字詞, 請以空格分開",
        component=discord.ui.TextInput(
            placeholder="",
            required=False,
        ),
    )

    _search_options = discord.ui.Label(
        text="搜尋選項",
        component=discord.ui.CheckboxGroup(
            required=False,
            options=[
                discord.CheckboxGroupOption(
                    label="英文字母不區分大小寫",
                    default=True,
                    value=AdvancedSearchOption.OPT_CASE_INSENSITIVE.value,
                ),
                discord.CheckboxGroupOption(
                    label="選項唯一時直接查詢價格",
                    default=True,
                    value=AdvancedSearchOption.OPT_SINGLE_IS_PERFECT.value,
                ),
                # discord.CheckboxGroupOption(
                #     label="Only search names",
                #     value="INAN",
                # ),
                discord.CheckboxGroupOption(
                    label="長度必須匹配",
                    value=AdvancedSearchOption.OPT_SAME_LENGTH.value,
                ),
                discord.CheckboxGroupOption(
                    label="字詞位置必須匹配",
                    value=AdvancedSearchOption.OPT_SAME_ABS_POSITION.value,
                ),
            ],
        ),
    )

    _reply_options = discord.ui.Label(
        text="回覆選項",
        component=discord.ui.RadioGroup(
            options=[
                discord.RadioGroupOption(
                    label="臨時訊息",
                    description="只有你才看得到的訊息, 一段時間後會自動刪除, 也可手動刪除",
                    value=ReplyOption.Ephemeral.value,
                    default=True,
                ),
                discord.RadioGroupOption(
                    label="私人訊息",
                    description="3分鐘後自動刪除",
                    value=ReplyOption.Direct.value,
                ),
            ]
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

    @property
    def master_keyword(self):
        assert isinstance(self._master_keyword.component, discord.ui.TextInput)
        return self._master_keyword.component.value

    @property
    def filter_keyword(self):
        assert isinstance(self._filter_keyword.component, discord.ui.TextInput)
        return self._filter_keyword.component.value

    @property
    def search_options(self):
        assert isinstance(self._search_options.component, discord.ui.CheckboxGroup)
        return set(
            [AdvancedSearchOption(val) for val in self._search_options.component.values]
        )

    @property
    def reply_option(self):
        assert isinstance(self._reply_options.component, discord.ui.RadioGroup)
        return ReplyOption(self._reply_options.component.value)
