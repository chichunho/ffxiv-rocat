import csv
import json


def main():
    item_dict: dict[str, str] = {}
    with open("market/data/item.csv", newline="", encoding="utf-8") as in_f:
        reader = csv.reader(in_f)
        for lineno, row in enumerate(reader):
            if lineno < 6:
                print(row[23])
                continue
            if row[23] == "True":
                continue
            if len(row[1]) == 0:
                continue
            item_dict[str(row[0])] = str(row[1])
    with open("market/data/item.json", "w", encoding="utf-8") as out_f:
        json.dump(item_dict, out_f, ensure_ascii=False)


if __name__ == "__main__":
    main()
