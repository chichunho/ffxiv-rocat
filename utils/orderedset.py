from typing import Hashable, Iterable


class SimpleOrderedSet(Iterable):
    def __init__(self, src_iter: Iterable[Hashable]):
        self.set_ = set()
        self.list_ = []

        self.union(src_iter)

    def __iter__(self):
        yield from self.list_

    def __len__(self):
        return len(self.list_)

    def union(self, another_iter: Iterable[Hashable]):
        for x in another_iter:
            self.add(x)

    def add(self, x: Hashable):
        if x in self.set_:
            return
        self.set_.add(x)
        self.list_.append(x)

    def remove(self, x: Hashable):
        try:
            self.set_.remove(x)
            self.list_.remove(x)
        except ValueError:
            pass
