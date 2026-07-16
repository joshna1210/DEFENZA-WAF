"""
Compiles and deploys WAFLogger.sol to whatever WEB3_PROVIDER_URL points at
(e.g. a local Ganache instance: `ganache --port 8545`).

Usage:
    python scripts/deploy.py

Prints the deployed contract address — put it in your .env as
CONTRACT_ADDRESS.
"""
import os
import json
import solcx
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

WEB3_PROVIDER_URL = os.getenv("WEB3_PROVIDER_URL", "http://127.0.0.1:8545")
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")

CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "..", "contracts", "WAFLogger.sol")
ABI_OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "abi", "WAFLogger.json")


def compile_contract():
    solcx.install_solc("0.8.19")
    with open(CONTRACT_PATH) as f:
        source = f.read()

    compiled = solcx.compile_source(
        source, output_values=["abi", "bin"], solc_version="0.8.19"
    )
    contract_id, contract_interface = list(compiled.items())[0]
    return contract_interface["abi"], contract_interface["bin"]


def deploy():
    w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to {WEB3_PROVIDER_URL} — is Ganache running?")

    abi, bytecode = compile_contract()

    if DEPLOYER_PRIVATE_KEY:
        account = w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)
        sender = account.address
    else:
        # Fall back to the first unlocked Ganache account (dev only)
        sender = w3.eth.accounts[0]
        account = None

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Contract.constructor().build_transaction(
        {
            "from": sender,
            "nonce": w3.eth.get_transaction_count(sender),
            "gas": 3_000_000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    if account:
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    else:
        tx_hash = w3.eth.send_transaction(tx)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"WAFLogger deployed at: {receipt.contractAddress}")

    with open(ABI_OUT_PATH, "w") as f:
        json.dump(abi, f, indent=2)
    print(f"ABI written to {ABI_OUT_PATH}")


if __name__ == "__main__":
    deploy()
