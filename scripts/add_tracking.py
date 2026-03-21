import json
import os
import re
import time
from pathlib import Path

import requests


KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
API_URL = "https://api.keepa.com/tracking"

MAIN_DOMAIN_ID = int(os.environ.get("MAIN_DOMAIN_ID", "5"))
MAX_TRACKING = int(os.environ.get("MAX_TRACKING", "50"))
IN_FILE = os.environ.get("IN_FILE", "asins_protein.json")

ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")


def load_asins(path_str: str) -> list[str]:
    path = Path(path_str)
    if not path.exists():
        print(f"[SKIP] input file not found: {path}")
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        if "asins" in data and isinstance(data["asins"], list):
            raw_asins = data["asins"]
        elif "asinList" in data and isinstance(data["asinList"], list):
            raw_asins = data["asinList"]
        else:
            raw_asins = []
    elif isinstance(data, list):
        raw_asins = data
    else:
        raw_asins = []

    cleaned = []
    seen = set()

    for value in raw_asins:
        if not isinstance(value, str):
            continue
        asin = value.strip().upper()
        if not ASIN_PATTERN.fullmatch(asin):
            print(f"[SKIP] invalid asin format in file: {value}")
            continue
        if asin in seen:
            continue
        seen.add(asin)
        cleaned.append(asin)

    return cleaned[:MAX_TRACKING]


def add_tracking(asin: str) -> bool:
    payload = {
        "asin": asin,
        "mainDomainId": MAIN_DOMAIN_ID,
    }

    print(f"[DEBUG] request asin={asin} payload={json.dumps(payload, ensure_ascii=False)}")

    response = requests.post(
        API_URL,
        params={"key": KEEPA_API_KEY, "type": "add"},
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if response.ok:
        print(f"[OK] tracking added: {asin} body={response.text[:300]}")
        return True

    print(
        f"[NG] tracking failed: {asin} "
        f"status={response.status_code} body={response.text[:500]}"
    )
    return False


def main() -> None:
    asins = load_asins(IN_FILE)

    print(f"[INFO] IN_FILE={IN_FILE}")
    print(f"[INFO] MAIN_DOMAIN_ID={MAIN_DOMAIN_ID}")
    print(f"[INFO] valid_asins={len(asins)}")
    print(f"[INFO] sample_asins={asins[:10]}")

    if not asins:
        print("[SKIP] no valid ASINs")
        return

    success = 0
    failed = 0

    for asin in asins:
        if add_tracking(asin):
            success += 1
        else:
            failed += 1
        time.sleep(1)

    print(f"[DONE] tracking success={success}, failed={failed}, domain={MAIN_DOMAIN_ID}")


if __name__ == "__main__":
    main()