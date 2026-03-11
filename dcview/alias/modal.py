from dcview.item_search import ItemSearchView


class AliasModalView(ItemSearchView):
    def __init__(self):
        super().__init__(title="新增物品別名")
