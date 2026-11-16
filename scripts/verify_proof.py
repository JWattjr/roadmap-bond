"""Read-only verification of the final Roadmap Bond StudioNet release."""

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
PROOF = json.loads((ROOT / "deploy/proof.json").read_text(encoding="utf-8"))
RPC = "https://studio.genlayer.com/api"
EXPLORER = "https://explorer-studio.genlayer.com"
HEADERS = {"User-Agent": "Mozilla/5.0 RoadmapBond/1.0", "Accept": "application/json"}
MAX_ATTEMPTS = 8
LAST_REQUEST = 0.0
EXPECTED_CONTRACTS = {"BondBoard": "bond_board.py", "PromiseJudge": "promise_judge.py"}


def retry_delay(attempt):
    return min(2 ** attempt, 30)


def request(method, url, **kwargs):
    global LAST_REQUEST
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", 45)
    for attempt in range(MAX_ATTEMPTS):
        wait = 2.1 - (time.monotonic() - LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        try:
            response = requests.request(method, url, **kwargs)
        except requests.exceptions.RequestException:
            LAST_REQUEST = time.monotonic()
            if attempt == MAX_ATTEMPTS - 1:
                raise
            print("Transient read timeout; retrying", flush=True)
            time.sleep(retry_delay(attempt))
            continue
        LAST_REQUEST = time.monotonic()
        if response.status_code in (429, 500, 502, 503, 504) and attempt < MAX_ATTEMPTS - 1:
            print("Transient HTTP " + str(response.status_code) + "; retrying", flush=True)
            time.sleep(retry_delay(attempt))
            continue
        response.raise_for_status()
        return response
    raise RuntimeError("HTTP read retries exhausted for " + url)


def rpc(method, params):
    response = request("POST", RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    body = response.json()
    if body.get("error"):
        raise RuntimeError(method + ": " + str(body["error"]))
    return body.get("result")


def nested_address_objects(value):
    if isinstance(value, dict):
        if "type" in value and "address" in value:
            yield value
        for child in value.values():
            yield from nested_address_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_address_objects(child)


def verify_manifest_shape():
    if PROOF.get("network") != "StudioNet" or int(PROOF.get("chainId", -1)) != 61999:
        raise RuntimeError("Proof manifest must identify StudioNet chain 61999")
    contracts = PROOF.get("contracts", {})
    if set(contracts) != set(EXPECTED_CONTRACTS):
        raise RuntimeError("Final proof must contain only BondBoard and PromiseJudge contract addresses")
    if PROOF.get("releaseStatus") != "DEPLOYED":
        raise RuntimeError("No completed final contract deployment is recorded")
    for name, expected_source in EXPECTED_CONTRACTS.items():
        item = contracts[name]
        if item.get("source") != expected_source:
            raise RuntimeError(name + " source path is not the final contract file")
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", str(item.get("address", ""))):
            raise RuntimeError(name + " address is missing or malformed")
        if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
            raise RuntimeError(name + " source SHA-256 is missing or malformed")


def verify_contracts():
    for name, item in PROOF["contracts"].items():
        address = item["address"]
        source_path = ROOT / "contracts" / item["source"]
        actual_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual_sha != item["sha256"]:
            raise RuntimeError(name + " source no longer matches the deployed manifest hash")
        result = request("GET", EXPLORER + "/api/address/" + address).json()
        matches = [obj for obj in nested_address_objects(result) if str(obj.get("address", "")).lower() == address.lower()]
        if not matches or not any(obj.get("type") == "CONTRACT" for obj in matches):
            raise RuntimeError(name + " Explorer record does not identify this address as a contract")
        link = EXPLORER + "/address/" + address
        page = request("GET", link)
        parsed = urlparse(page.url)
        if parsed.hostname != "explorer-studio.genlayer.com" or address.lower() not in parsed.path.lower():
            raise RuntimeError(name + " direct Explorer link did not open this StudioNet contract record")
        print("CONTRACT", name, address, "direct StudioNet Explorer address verified", flush=True)


def verify_transactions():
    chain_id = int(rpc("eth_chainId", []), 16)
    if chain_id != 61999:
        raise RuntimeError("RPC is on chain " + str(chain_id) + ", expected StudioNet 61999")
    transactions = PROOF.get("transactions", {})
    if not transactions:
        raise RuntimeError("No deployment or case transaction hashes are recorded")
    for label, tx_hash in transactions.items():
        if not re.fullmatch(r"0x[0-9a-fA-F]{64}", str(tx_hash)):
            raise RuntimeError(label + " transaction hash is malformed")
        tx = rpc("eth_getTransactionByHash", [tx_hash])
        status = tx.get("status_name", tx.get("status")) if tx else None
        if status not in ("FINALIZED", 7, "7"):
            raise RuntimeError(label + " is not finalized on StudioNet RPC: " + str(status))
        request("GET", EXPLORER + "/api/transactions/" + tx_hash)
        print("TX", label, tx_hash, "finalized on StudioNet RPC; Explorer record readable", flush=True)


def verify_source_commit():
    expected = PROOF.get("sourceCommit")
    if not expected:
        raise RuntimeError("Final source commit is not recorded")
    try:
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        raise RuntimeError("Cannot read the repository commit needed to verify source identity")
    if actual != expected:
        raise RuntimeError("Checked-out source commit differs from the deployed proof")


def main():
    verify_manifest_shape()
    verify_source_commit()
    verify_contracts()
    verify_transactions()
    print("Read-only proof verification passed. The Portal form was not submitted.", flush=True)


if __name__ == "__main__":
    main()
