"""Kept separate from backend/app/services/blockchain_service.py so this
package can be run standalone (e.g. as a cron job / cli) without importing
the whole FastAPI backend."""
from app.web3_client import get_contract


def get_batch(contract_address: str, index: int):
    w3, contract = get_contract(contract_address)
    return contract.functions.getBatch(index).call()
