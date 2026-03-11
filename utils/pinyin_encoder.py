import json
from pypinyin import lazy_pinyin, FIRST_LETTER


def main():
    with open("market/data/item.json", "r", encoding="utf-8") as in_f:
        item_src: dict[str, str] = json.load(in_f)

    pinyin_dict: dict[str, str] = {}
    # oversized_pinyin: set[str] = set()
    # max_count = 1
    for code, name in item_src.items():
        pinyin_short = "".join(lazy_pinyin(name, FIRST_LETTER))
        pinyin_dict[code] = pinyin_short

    with open("market/data/item_pinyin.json", "w", encoding="utf-8") as out_f:
        json.dump(pinyin_dict, out_f, ensure_ascii=False)

    # print(max_count)
    # print(oversized_pinyin)


if __name__ == "__main__":
    main()
