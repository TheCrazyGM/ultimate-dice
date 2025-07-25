import requests
import dataset
import sys

API_URL = "http://localhost:8000/api/roll"
DB_URL = "sqlite:///dice_fairness.db"
TABLE_NAME = "fast_rolls"

# Dice roll parameters (customize as needed)
DICE_TYPE = "d6"
DICE_COUNT = 3
MODIFIER = 0
LABEL = "fast_3d6"

if __name__ == "__main__":
    db = dataset.connect(DB_URL)
    table = db[TABLE_NAME]
    for i in range(100):
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
                print(f"Roll {i+1} failed: {data.get('message')}", file=sys.stderr)
                continue
            # Save all relevant info to DB
            table.insert({
                "roll_index": i+1,
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
            })
            print(f"Roll {i+1}: {data.get('result')}")
        except Exception as e:
            print(f"Error on roll {i+1}: {e}", file=sys.stderr)
