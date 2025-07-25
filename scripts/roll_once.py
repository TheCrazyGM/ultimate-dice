#!/usr/bin/env python3
"""roll_once.py
A convenience script that performs **one** dice roll via the Ultimate Dice API and
persists the outcome to a SQLite DB.  Intended for use with cron so you can
schedule periodic rolls (e.g. every minute) to accumulate a very long-running
dataset without keeping a script alive.

Example crontab entry (roll every minute):
    * * * * * /path/to/venv/bin/python3 /path/to/ultimate-dice/scripts/roll_once.py >> $HOME/roll_once.log 2>&1
"""

import sys
from datetime import datetime

import dataset
import requests

API_URL = "https://dice.thecrazygm.com/api/roll"  # Update if your server runs elsewhere
DB_URL = "sqlite:///dice_fairness.db"
TABLE_NAME = "once_rolls"

# Dice roll parameters (customize as needed)
DICE_TYPE = "d6"
DICE_COUNT = 3
MODIFIER = 0
LABEL = "cron_3d6"


def main() -> None:
    """Perform exactly one roll and store the result."""
    db = dataset.connect(DB_URL)
    table = db[TABLE_NAME]

    try:
        resp = requests.post(
            API_URL,
            json={
                "dice_type": DICE_TYPE,
                "dice_count": DICE_COUNT,
                "modifier": MODIFIER,
                "label": LABEL,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            print(f"Roll failed: {data.get('message')}", file=sys.stderr)
            sys.exit(1)

        # Insert record – roll_index is always 1 because this script only rolls once
        table.insert(
            {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
                "dice_type": DICE_TYPE,
                "dice_count": DICE_COUNT,
                "modifier": MODIFIER,
                "label": LABEL,
                "result": ",".join(map(str, data.get("result", []))),
                "proof": data.get("proof"),
                "server_seed": data.get("server_seed"),
                "client_seed": data.get("client_seed"),
                "nonce": data.get("nonce"),
                "block_num": data.get("block_num"),
                "roll_id": data.get("roll_id"),
            }
        )
        print(f"Rolled {data.get('result')}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
