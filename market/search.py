# ItemKeyword parser tests
# raw master is a single str, all spaces should be kept, char is not unique, cannot be empty
# raw support is a list of substr separated by spaces, all substr is unqiue, can be empty

# length refers to the length of the raw master union the raw support
# (raw_master='nxrg', raw_support='') => (length=4, min_lenght=4, raw_master='nxrg', master='nxrg', supports={}, seg={})
# (raw_master='nx', raw_support='革') => (length=3, min_lenght=3, raw_master='nx', master='nx', supports={'革'}, seg={})
# (raw_master='nx革', raw_support='革') => (length=3, min_lenght=3, raw_master='nx革', master='nx', supports={'革'}, seg={(2, 1): '革'})

# min_length refers to the length of the raw master after stripping the wildcard char union the raw support
# (raw_master='nx**', raw_support='') => (length=4, min_length=2, raw_master='nx**', master='nx', supports={}, seg={})

# any non-ascii char in raw master treat as support keywords, the raw master non-ascii char positional info stored in seg
# (raw_master='ns*革', raw_support='') => (length=4, min_length=4, raw_master='ns*革', master='ns', supports{'革'}, seg={(3, 1): '革'})

# if the raw master does not contain any ascii char, then the first non-ascii char would be the master
# (raw_master='*夏*革', raw_support='') => (length=4, min_length=3, raw_master='*夏*革', master='夏', supports={'革'}, seg={(1, 1): '夏', (3, 1): '革'})


import shlex
from typing import Iterable, Protocol

from rapidfuzz import fuzz

from market.enums import AdvancedSearchOption
from market.model import ItemLike
from utils.orderedset import SimpleOrderedSet


class ItemKeyword:
    def __init__(self, raw_master: str, raw_support: str, wildcard_char: str = "*"):
        self.wildcard_char = wildcard_char
        self.raw_master = raw_master

        ascii_texts: list[list[str]] = [[]]
        nonascii_texts: list[list[str]] = [[]]
        list_ptr = ascii_texts
        tail_ptr = list_ptr[-1]

        self.pos: dict[tuple[int, int] : str] = {}

        for idx, c in enumerate(raw_master):
            if c != wildcard_char and (
                (c.isascii() and list_ptr is ascii_texts)
                or (not c.isascii() and list_ptr is nonascii_texts)
            ):
                tail_ptr.append(c)
                continue

            # update the list_ptr to point to the new tail of current list
            if c == wildcard_char:
                if len(tail_ptr) > 0:
                    self.pos[idx - len(tail_ptr), len(tail_ptr)] = "".join(tail_ptr)
                    list_ptr.append([])
                    tail_ptr = list_ptr[-1]
                continue

            # switch the list_ptr and append the c
            if len(tail_ptr) > 0:
                list_ptr.append([])
                self.pos[idx - len(tail_ptr), len(tail_ptr)] = "".join(tail_ptr)
            list_ptr = ascii_texts if list_ptr is nonascii_texts else nonascii_texts
            tail_ptr = list_ptr[-1]
            tail_ptr.append(c)

        if len(tail_ptr) > 0:
            self.pos[len(raw_master) - len(tail_ptr), len(tail_ptr)] = "".join(tail_ptr)

        self.master = "".join(["".join(eles) for eles in ascii_texts])
        filter_words = SimpleOrderedSet(
            ["".join(eles) for eles in nonascii_texts if len(eles) > 0]
        )
        filter_words.union(shlex.split(raw_support))
        if len(self.master) == 0 and len(filter_words) > 0:
            self.master, self.filter_words = (
                filter_words.list_[0],
                filter_words.list_[1:],
            )
        else:
            self.filter_words = filter_words.list_

        master_list = list(raw_master.replace("*", ""))

        self.length = len(master_list) + max(
            len(raw_master) - len(master_list),  # number of wildcard char in raw master
            len(
                filter_words.set_.difference(set(master_list))
            ),  # the number of substr that are not in raw master
        )
        self.min_length = max(
            1,
            len(raw_master.strip("*"))
            + len(filter_words.set_.difference(set(master_list))),
        )

    def __len__(self):
        return self.length

    def __int__(self):
        return int(self.master)

    def __hash__(self):
        return hash(self.raw_master)

    def __str__(self):
        return f"ItemKeyword(length={len(self)}, min_length={self.min_length}, raw_master='{self.raw_master}', master='{self.master}', filter_words={self.filter_words}, pos={self.pos})"


class AdvancedCheck(Protocol):
    def __call__(self, candidate: ItemLike) -> bool: ...


class Contains(AdvancedCheck):
    def __init__(self, keyword: ItemKeyword):
        self.support_keywords = keyword.filter_words

    def __call__(self, candidate: ItemLike) -> bool:
        for keyword in self.support_keywords:
            if fuzz.partial_ratio(candidate.name, keyword) < 100:
                return False
        return True


class StrictLength(AdvancedCheck):
    def __init__(self, keyword: ItemKeyword):
        self.keyword = keyword

    def __call__(self, candidate: ItemLike) -> bool:
        return len(self.keyword) == len(candidate.name)


class StrictPosition(AdvancedCheck):
    def __init__(self, keyword: ItemKeyword):
        self.keyword = keyword

    def __call__(self, candidate: ItemLike) -> bool:
        for (start_idx, length), segment in self.keyword.pos.items():
            if start_idx >= len(candidate.name):
                return False
            if candidate.name[start_idx : (start_idx + length)] != segment:
                return False
        return True


class AdvancedChecker:
    def __init__(self, keyword: ItemKeyword, options: Iterable[AdvancedSearchOption]):
        self.keyword = keyword
        self.checks: set[AdvancedCheck] = set()
        self._generate_checks(options)

    def _generate_checks(self, options: Iterable[AdvancedSearchOption]):
        for option in options:
            match option:
                case AdvancedSearchOption.OPT_CONTAINS:
                    self.checks.add(Contains(self.keyword))
                case AdvancedSearchOption.OPT_SAME_LENGTH:
                    self.checks.add(StrictLength(self.keyword))
                case AdvancedSearchOption.OPT_SAME_ABS_POSITION:
                    self.checks.add(StrictPosition(self.keyword))

    def check(self, candidate: ItemLike):
        for is_valid in self.checks:
            if not is_valid(candidate):
                return False
        return True
