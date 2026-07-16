"""
Quick manual sanity check against a deployed WAFLogger contract.
Usage: python scripts/interact.py
"""
import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URL", "http://127.0.0.1:8545")))
ABI_PATH = os.path.join(os.path.dirname(__file__), "..", "abi", "WAFLogger.json")

with open(ABI_PATH) as f:
    abi = json.load(f)

contract_address = os.getenv("CONTRACT_ADDRESS")
contract = w3.eth.contract(address=contract_address, abi=abi)

count = contract.functions.batchCount().call()
print(f"Total batches recorded on-chain: {count}")

if count > 0:
    latest = contract.functions.getBatch(count - 1).call()
    print(f"Latest batch: merkleRoot={latest[0].hex()} logCount={latest[1]} timestamp={latest[2]} submitter={latest[3]}")
