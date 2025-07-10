import hashlib
import hmac
import logging
import secrets
from datetime import datetime

from bson.objectid import ObjectId
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

# Blockchain access via Hive Nectar
try:
    from nectar.blockchain import (
        Blockchain,
    )  # hive-nectar package mirrors beem.blockchain
except ImportError:
    # Fallback in case import name differs or package missing
    Blockchain = None


# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["ultimate_dice"]
rolls_collection = db["dice_rolls"]

app = Flask(__name__)

# Initialize blockchain interface if available
blockchain = None
if Blockchain is not None:
    try:
        blockchain = Blockchain()
    except Exception as e:
        print(f"Warning: Failed to initialize Hive blockchain interface: {e}")


@app.route("/verify")
def verify_page():
    return render_template("proof_verify.html")


# Helper to roll dice
DICE_SIDES = {"d4": 4, "d6": 6, "d8": 8, "d10": 10, "d12": 12, "d20": 20, "d100": 100}


def provably_fair_roll(dice_type, dice_count, server_seed, client_seed, nonce):
    sides = DICE_SIDES.get(dice_type)
    if not sides:
        raise ValueError("Unsupported dice type")
    # Compose message: client_seed:nonce
    message = f"{client_seed}:{nonce}".encode()
    # HMAC-SHA256(server_seed, message)
    digest = hmac.new(server_seed.encode(), message, hashlib.sha256).hexdigest()
    # Use digest to generate dice rolls
    results = []
    for i in range(dice_count):
        # Take 8 hex digits per die (32 bits, more than enough)
        start = i * 8
        end = start + 8
        chunk = digest[start:end]
        if len(chunk) < 8:
            # Extend digest if needed
            chunk += digest[: 8 - len(chunk)]
        num = int(chunk, 16)
        roll = (num % sides) + 1
        results.append(roll)
    return results, digest


@app.route("/")
def index():
    # Show last 10 rolls (most recent first)
    rolls = list(rolls_collection.find().sort("timestamp", -1).limit(10))
    for roll in rolls:
        roll["id"] = str(roll["_id"])
    return render_template("index.html", rolls=rolls)


@app.route("/api/rolls", methods=["GET"])
def api_rolls():
    # Return last 10 rolls as JSON
    rolls = list(rolls_collection.find().sort("timestamp", -1).limit(10))
    return jsonify(
        [
            {
                "id": str(r["_id"]),
                "dice_type": r["dice_type"],
                "roll_result": r["roll_result"],
                "proof": r["proof"],
                "timestamp": r["timestamp"].isoformat(),
                "server_seed": r["server_seed"],
                "client_seed": r["client_seed"],
                "nonce": r["nonce"],
                "modifier": r["modifier"],
                "label": r["label"],
                "block_num": r.get("block_num"),
            }
            for r in rolls
        ]
    )


@app.route("/roll/<string:roll_id>")
def roll_detail(roll_id):
    roll = rolls_collection.find_one({"_id": ObjectId(roll_id)})
    if roll is None:
        return jsonify({"success": False, "message": "Roll not found"}), 404
    # Recompute result and proof for verification
    try:
        recomputed_result, recomputed_proof = provably_fair_roll(
            roll["dice_type"].split("x")[-1],
            int(roll["dice_type"].split("x")[0]) if "x" in roll["dice_type"] else 1,
            roll["server_seed"],
            roll["client_seed"],
            roll["nonce"],
        )
    except Exception as e:
        recomputed_result, recomputed_proof = [], f"Error: {e}"
    verified = (
        recomputed_proof == roll["proof"]
        and ",".join(map(str, recomputed_result)) == roll["roll_result"]
    )
    return render_template(
        "roll_detail.html",
        roll=roll,
        verified=verified,
        recomputed_result=recomputed_result,
        recomputed_proof=recomputed_proof,
    )


@app.route("/api/roll", methods=["POST"])
def api_roll():
    data = request.json
    dice_type = data.get("dice_type")
    dice_count = int(data.get("dice_count", 1))
    if dice_type not in DICE_SIDES:
        return jsonify({"success": False, "message": "Unsupported dice type"}), 400
    if not (1 <= dice_count <= 20):
        return jsonify({"success": False, "message": "Dice count must be 1-20"}), 400
    # Generate seeds from Hive blockchain if available
    block_num = None
    if blockchain is not None:
        try:
            latest_block = blockchain.get_current_block()
            block_data = (
                latest_block.as_json()
                if hasattr(latest_block, "as_json")
                else dict(latest_block)
            )
            logging.info(f"Fetched latest Hive block object: {latest_block}")
            logging.info(f"Block data keys: {list(block_data.keys())}")
            # logging.info(f"Block data: {block_data}")
            # Common field names – adjust if Nectar differs
            block_num = (
                int(block_data.get("id")) if block_data.get("id") is not None else None
            )
            server_seed = block_data.get("block_id") or secrets.token_hex(16)
            client_seed_base = block_data.get(
                "transaction_merkle_root"
            ) or secrets.token_hex(8)
            salt = secrets.token_hex(4)  # 8-hex-char per-request salt
            client_seed = f"{client_seed_base}{salt}"
        except Exception as e:
            print(f"Hive fetch error: {e}")
            server_seed = secrets.token_hex(16)
            client_seed = f"{secrets.token_hex(8)}{secrets.token_hex(4)}"
    else:
        server_seed = secrets.token_hex(16)
        client_seed = f"{secrets.token_hex(8)}{secrets.token_hex(4)}"
    nonce = block_num or 0
    logging.info(
        f"Using seeds - server: {server_seed}, client: {client_seed}, nonce: {nonce}"
    )
    results, proof = provably_fair_roll(
        dice_type, dice_count, server_seed, client_seed, nonce
    )
    # Store in DB
    modifier = int(data.get("modifier", 0))
    label = data.get("label", None)
    roll_doc = {
        "dice_type": f"{dice_count}x{dice_type}",
        "roll_result": ",".join(map(str, results)),
        "proof": proof,
        "server_seed": server_seed,
        "client_seed": client_seed,
        "nonce": nonce,
        "modifier": modifier,
        "block_num": block_num,
        "label": label,
        "timestamp": datetime.utcnow(),
    }
    inserted = rolls_collection.insert_one(roll_doc)
    roll_id = str(inserted.inserted_id)
    return jsonify(
        {
            "success": True,
            "result": results,
            "proof": proof,
            "server_seed": server_seed,
            "client_seed": client_seed,
            "nonce": nonce,
            "block_num": block_num,
            "roll_id": roll_id,
        }
    )


# API endpoint to verify roll
@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.json
    dice_type = data.get("dice_type")
    dice_count = int(data.get("dice_count", 1))
    server_seed = data.get("server_seed")
    client_seed = data.get("client_seed")
    nonce = int(data.get("nonce", 0))
    expected_result = data.get("result")
    expected_proof = data.get("proof")
    if not all(
        [
            dice_type,
            dice_count,
            server_seed,
            client_seed,
            expected_result,
            expected_proof,
        ]
    ):
        return jsonify({"success": False, "message": "Missing parameters"}), 400
    try:
        recomputed_result, recomputed_proof = provably_fair_roll(
            dice_type, dice_count, server_seed, client_seed, nonce
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
    # Compare
    result_match = list(map(str, recomputed_result)) == list(map(str, expected_result))
    proof_match = recomputed_proof == expected_proof
    return jsonify(
        {
            "success": result_match and proof_match,
            "result_match": result_match,
            "proof_match": proof_match,
            "recomputed_result": recomputed_result,
            "recomputed_proof": recomputed_proof,
        }
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
