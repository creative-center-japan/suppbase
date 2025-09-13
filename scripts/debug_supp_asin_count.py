import json, pathlib, sys

p = pathlib.Path("data/asins_supplements_jp.json")
if not p.exists():
    print("supplement asin file: MISSING")
    sys.exit(0)

try:
    d = json.load(p.open(encoding="utf-8"))
    if isinstance(d, list):
        print("supplement asins count =", len(d))
        print("is_empty_array =", len(d) == 0)
    else:
        print("supplement asins count = N/A (not a list)")
except Exception as e:
    print("supplement asin file: INVALID:", e)
