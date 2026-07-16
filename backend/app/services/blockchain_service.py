"""
Batched blockchain audit logging.

Instead of writing every request to the chain (slow, expensive, serializes
on nonce), we periodically batch the last N unbatched traffic logs, compute
a Merkle root of their hashes, and write ONE transaction containing that
root + batch metadata to the WAFLogger smart contract (see
blockchain/contracts/WAFLogger.sol).

Gated behind settings.BLOCKCHAIN_ENABLED — with it off (default), batching
still runs and computes Merkle roots, but "writes" are simulated and stored
locally in `blockchain_batches` so the dashboard has data to show without a
running Ganache instance.
"""
from datetime import datetime
from bson import ObjectId

from app.config.database import traffic_logs, blockchain_batches
from app.config.settings import settings
from app.utils.helpers import hash_log_entry, now_utc
from app.utils.logger import get_logger

logger = get_logger("blockchain_service")


def merkle_root(hashes: list[str]) -> str:
    if not hashes:
        return ""
    layer = hashes[:]
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])  # duplicate last if odd
        next_layer = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            import hashlib
            next_layer.append(hashlib.sha256(combined.encode()).hexdigest())
        layer = next_layer
    return layer[0]


async def run_batch_job():
    """Called on a schedule (see main.py startup) — picks up unbatched
    traffic logs, hashes them, computes a Merkle root, and persists/writes
    the batch."""
    cursor = traffic_logs().find(
        {"blockchain_batch_id": None, "analyzed": True}
    ).limit(settings.BATCH_LOG_SIZE)

    docs = [doc async for doc in cursor]
    if not docs:
        return

    hashes = [hash_log_entry({**doc, "_id": str(doc["_id"])}) for doc in docs]
    root = merkle_root(hashes)

    batch_doc = {
        "created_at": now_utc(),
        "log_count": len(docs),
        "merkle_root": root,
        "log_hashes": hashes,
        "tx_hash": None,
        "on_chain": False,
    }

    if settings.BLOCKCHAIN_ENABLED:
        tx_hash = await _write_to_chain(root, len(docs))
        batch_doc["tx_hash"] = tx_hash
        batch_doc["on_chain"] = tx_hash is not None
    else:
        logger.info(f"[mock] Would write Merkle root {root} for {len(docs)} logs to chain")

    result = await blockchain_batches().insert_one(batch_doc)
    batch_id = str(result.inserted_id)

    ids = [doc["_id"] for doc in docs]
    await traffic_logs().update_many(
        {"_id": {"$in": ids}}, {"$set": {"blockchain_batch_id": batch_id}}
    )
    logger.info(f"Batched {len(docs)} logs into blockchain_batch {batch_id}")


async def _write_to_chain(root: str, count: int) -> str | None:
    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        if not w3.is_connected():
            logger.warning("Web3 provider not reachable, skipping on-chain write")
            return None
        if not settings.CONTRACT_ADDRESS or not settings.DEPLOYER_PRIVATE_KEY:
            logger.warning("CONTRACT_ADDRESS / DEPLOYER_PRIVATE_KEY not set, skipping on-chain write")
            return None

        import json, os
        abi_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "blockchain", "abi", "WAFLogger.json")
        with open(abi_path) as f:
            abi = json.load(f)

        contract = w3.eth.contract(address=settings.CONTRACT_ADDRESS, abi=abi)
        account = w3.eth.account.from_key(settings.DEPLOYER_PRIVATE_KEY)

        tx = contract.functions.logBatch(root, count).build_transaction(
            {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "gas": 200000,
                "gasPrice": w3.eth.gas_price,
            }
        )
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()
    except Exception:
        logger.exception("Failed to write batch to chain")
        return None


async def list_batches(limit: int = 50):
    cursor = blockchain_batches().find().sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        doc.pop("log_hashes", None)  # keep list responses light
        results.append(doc)
    return results
