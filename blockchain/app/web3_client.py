"""
Thin wrapper the backend can reuse if you want richer chain interactions
than the batch write in backend/app/services/blockchain_service.py (e.g. a
CLI or admin tool to read batch history directly)."""
import os
import json
from web3 import Web3

WEB3_PROVIDER_URL = os.getenv("WEB3_PROVIDER_URL", "http://127.0.0.1:8545")
ABI_PATH = os.path.join(os.path.dirname(__file__), "..", "abi", "WAFLogger.json")


def get_contract(contract_address: str):
    w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
    with open(ABI_PATH) as f:
        abi = json.load(f)
    return w3, w3.eth.contract(address=contract_address, abi=abi)
