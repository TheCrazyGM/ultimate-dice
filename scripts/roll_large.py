import requests
import dataset
import sys

API_URL = "http://localhost:8000/api/roll"
DB_URL = "sqlite:///dice_fairness.db"
TABLE_NAME = "large_fast_rolls"

# Dice roll parameters for 3d6
DICE_TYPE = "d6"
DICE_COUNT = 3
MODIFIER = 0
LABEL = "large_fast_3d6"
N_ROLLS = 5000  # You can increase this if you want even more data

if __name__ == "__main__":
    db = dataset.connect(DB_URL)
    table = db[TABLE_NAME]
    for i in range(N_ROLLS):
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
            if (i+1) % 100 == 0:
                print(f"Completed {i+1} rolls...")
        except Exception as e:
            print(f"Error on roll {i+1}: {e}", file=sys.stderr)
