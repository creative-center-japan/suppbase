import os
import json
import time
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]

# Keepa domain: 1=JP, 2=US
DOMAIN_ID = int(os.environ.get("DOMAIN_ID", "2"))
BESTSELLERS_API = "https://api.keepa.com/bestsellers"

CATEGORY_ID = os.environ.get("CATEGORY_ID")
OUT_FILE = os.environ.get("OUT_FILE", "asins_us_bestsellers.json")

RETRY = int(os.environ.get("RETRY", "3"))
DEFAULT_SLEEP = int(os.environ.get("SLEEP", "60"))


def write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_asins(data):
    if not isinstance(data, dict):
        return []

    best = data.get("bestSellersList")

    if isinstance(best, dict):
        # もし dict 形式なら
        return best.get("asinList") or []

    if isinstance(best, list):
        # list の中身が ASIN文字列の配列
        if best and all(isinstance(x, str) for x in best):
            return best

        # list の中身が dict の配列
        asins = []
        for item in best:
            if isinstance(item, dict):
                asin = item.get("asin")
                if isinstance(asin, str) and asin:
                    asins.append(asin)
        return asins

    # API が直接 asinList を返すケース
    asin_list = data.get("asinList")
    if isinstance(asin_list, list):
        return [x for x in asin_list if isinstance(x, str) and x]

    return []


if not CATEGORY_ID:
    write_json(OUT_FILE, [])
    print("[ERROR][US] CATEGORY_ID not set")
    raise SystemExit(1)

for i in range(RETRY):
    try:
        r = requests.get(
            BESTSELLERS_API,
            params={
                "key": KEEPA_API_KEY,
                "domain": DOMAIN_ID,
                "category": CATEGORY_ID,
            },
            timeout=60,
        )
    except requests.RequestException as e:
        print(f"[ERROR][US] request failed (retry {i+1}/{RETRY}): {e}")
        if i < RETRY - 1:
            time.sleep(DEFAULT_SLEEP)
            continue
        write_json(OUT_FILE, [])
        raise SystemExit(1)

    if r.status_code == 429:
        sleep_sec = DEFAULT_SLEEP
        try:
            info = r.json()
            refill_in = info.get("refillIn")
            if isinstance(refill_in, int) and refill_in > 0:
                sleep_sec = max(5, int(refill_in / 1000) + 2)
            print(f"[429][US] rate limited (retry {i+1}/{RETRY}), sleep={sleep_sec}s, refillIn={refill_in}")
        except Exception:
            print(f"[429][US] rate limited (retry {i+1}/{RETRY}), sleep={sleep_sec}s")

        if i < RETRY - 1:
            time.sleep(sleep_sec)
            continue

        write_json(OUT_FILE, [])
        print("[ERROR][US] failed to fetch bestseller ASINs after retries")
        raise SystemExit(1)

    r.raise_for_status()
    data = r.json()
    asins = extract_asins(data)

    if not asins:
        write_json(OUT_FILE, [])
        print("[ERROR][US] fetched 0 bestseller ASINs")
        print(f"[DEBUG][US] response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        raise SystemExit(1)

    write_json(OUT_FILE, asins)
    print(f"[OK][US] fetched {len(asins)} bestseller ASINs -> {OUT_FILE}")
    raise SystemExit(0)

write_json(OUT_FILE, [])
print("[ERROR][US] unexpected end of fetch loop")
raise SystemExit(1)