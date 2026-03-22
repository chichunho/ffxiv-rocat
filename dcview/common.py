import discord

from dcview.enums import ReplyOption
from market.enums import AdvancedSearchOption


class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="確認")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        assert isinstance(self.view, discord.ui.View) or isinstance(
            self.view, discord.ui.LayoutView
        )
        self.view.stop()


class ItemMasterKeywordTextInput(discord.ui.Label):
    def __init__(self):
        super().__init__(
            text="物品關鍵字",
            description="物品編號, 正體中文字詞, 拚音首字母, 萬用字符(*)\n例如: 納夏鞣革, 納夏, nxrg, 納**g",
            component=discord.ui.TextInput(
                placeholder="",
            ),
        )


class ItemFilterKeywordTextInput(discord.ui.Label):
    def __init__(self):
        super().__init__(
            text="包含字詞",
            description="物品必包含以上字詞, 如有多個字詞, 請以空格分開",
            component=discord.ui.TextInput(
                placeholder="",
                required=False,
            ),
        )


class ItemSearchOptionCheckboxGroup(discord.ui.Label):
    def __init__(self):
        super().__init__(
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


class ReplyOptionRadioGroup(discord.ui.Label):
    def __init__(self):
        super().__init__(
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
