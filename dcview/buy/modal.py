from dcview.item_search import ItemSearchView


class BuyModalView(ItemSearchView):
    def __init__(self):
        super().__init__(title="FF14 繁中市場查價")
