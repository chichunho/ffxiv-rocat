import json
from opencc import OpenCC


def main():
    with open("market/data/item_cn.json", "r", encoding="utf-8") as in_f:
        item_src: dict[str, str] = json.load(in_f)

    tc2sc = OpenCC("t2s")

    sc_dict: dict[str, str] = {}
    for code, name in item_src.items():
        sc_dict[code] = tc2sc.convert(name)

    with open("market/data/item_sc.json", "w", encoding="utf-8") as out_f:
        json.dump(sc_dict, out_f, ensure_ascii=False)


if __name__ == "__main__":
    main()
