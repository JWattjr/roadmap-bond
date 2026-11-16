"""StudioNet helpers. Hashes are saved before receipt polling so runs can resume."""

import json
import os
import re
import time
from pathlib import Path

from eth_account import Account
from genlayer_py import create_client, studionet
from genlayer_py.provider import provider
from genlayer_py.types import TransactionHashVariant


ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 RoadmapBond/1.0"}
ROLES = [f"TEAM_{i}" for i in range(1, 6)] + ["CHALLENGER_1", "CHALLENGER_2", "OUTSIDER"]


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise RuntimeError("Missing ignored .env. Run python scripts/generate_keys.py first.")
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


load_env()
_post = provider.requests.post


def browser_post(url, **kwargs):
    kwargs["headers"] = {**kwargs.get("headers", {}), **UA}
    kwargs.setdefault("timeout", 45)
    method = kwargs.get("json", {}).get("method", "")
    read_only = method.startswith(("eth_get", "gen_get", "sim_get")) or method in ("eth_chainId", "gen_call")
    for attempt in range(4 if read_only else 1):
        try:
            response = _post(url, **kwargs)
            if response.status_code not in (429, 502, 503, 504) or not read_only or attempt == 3:
                return response
        except provider.requests.exceptions.RequestException:
            if not read_only or attempt == 3:
                raise
        print("Transient read-only RPC failure; retrying", flush=True)
        time.sleep(5 * (attempt + 1))


provider.requests.post = browser_post


def account(role="TEAM_1"):
    key = os.environ.get(role + "_PRIVATE_KEY", "")
    if not re.fullmatch(r"0x[0-9a-fA-F]{64}", key):
        raise RuntimeError("Missing or malformed " + role + "_PRIVATE_KEY in ignored .env")
    return Account.from_key(key)


def client(role="TEAM_1"):
    return create_client(chain=studionet, account=account(role))


def load_proof():
    return json.loads((ROOT / "deploy/proof.json").read_text(encoding="utf-8"))


def save_proof(proof):
    target = ROOT / "deploy/proof.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(proof, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(target)


def success(receipt):
    leader = ((receipt.get("consensus_data") or {}).get("leader_receipt") or [{}])[0]
    native = receipt.get("value_credited") is True and str(receipt.get("type")) == "0" and not receipt.get("consensus_data")
    executed = receipt.get("txExecutionResultName", leader.get("execution_result")) in ("SUCCESS", "FINISHED_WITH_RETURN")
    return receipt.get("status_name", receipt.get("status")) in ("FINALIZED", 7, "7") and (native or executed) and receipt.get("result_name") not in ("DISAGREE", "MAJORITY_DISAGREE")


def final(tx_hash, label, role="TEAM_1", allow_error=False, attempts=360):
    receipt_path = ROOT / "deploy/receipts" / (label + ".json")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(attempts):
        response = client(role).provider.make_request("eth_getTransactionByHash", [tx_hash])
        result = response.get("result") if isinstance(response, dict) else None
        state = result.get("status_name", result.get("status")) if result else None
        if result and state in ("CANCELED", 8, "8"):
            receipt_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(label, "CANCELED", flush=True)
            if not allow_error:
                raise RuntimeError("Transaction canceled; inspect " + str(receipt_path))
            return result
        if result and state in ("FINALIZED", 7, "7"):
            receipt_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            final_state = "FINALIZED_SUCCESS" if success(result) else "FINALIZED_ERROR"
            print(label, final_state, flush=True)
            if not success(result) and not allow_error:
                raise RuntimeError("Transaction execution failed; inspect " + str(receipt_path))
            return result
        if attempt % 6 == 0:
            print(label, state or "SUBMITTED", flush=True)
        time.sleep(10)
    raise RuntimeError("Still pending; rerun the same script to resume " + tx_hash)


def _follow_children(proof, parent_label, receipt, role="TEAM_1", depth=0):
    if depth >= 12:
        raise RuntimeError("Finality callback tree exceeded 12 levels")
    for index, child_hash in enumerate(receipt.get("triggered_transactions") or []):
        label = parent_label + "-child-" + str(index)
        existing = proof["transactions"].get(label)
        if existing and existing.lower() != child_hash.lower():
            raise RuntimeError("Callback transaction hash changed for " + label)
        proof["transactions"].setdefault(label, child_hash)
        save_proof(proof)
        child = final(child_hash, label, role=role, allow_error=True)
        _follow_children(proof, label, child, role=role, depth=depth + 1)


def tx(proof, label, address=None, method=None, args=None, code=None, role="TEAM_1", value=0, wait=True, allow_error=False):
    if label not in proof["transactions"]:
        marker = ROOT / "deploy/.pending-write.json"
        if marker.exists():
            raise RuntimeError("Resolve ambiguous submission in " + str(marker) + " before sending another write.")
        spent = sum(int(amount) for amount in proof.get("deposits", {}).values())
        if value and spent + int(value) > int(proof["approvedTotalWei"]):
            raise RuntimeError("Cumulative payable calls exceed the approved wei budget")
        marker.write_text(json.dumps({"label": label, "address": address, "method": method, "role": role, "valueWei": int(value)}), encoding="utf-8")
        instance = client(role)
        fees = {"feeValue": 0}
        handle = instance.deploy_contract(code, args=args or [], fees=fees) if code is not None else instance.write_contract(address, method, args=args or [], value=int(value), fees=fees)
        tx_hash = handle.hex() if hasattr(handle, "hex") else str(handle)
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash
        proof["transactions"][label] = tx_hash
        if value:
            proof.setdefault("deposits", {})[label] = int(value)
        save_proof(proof)
        marker.unlink()
        print(label, "SUBMITTED", flush=True)
    tx_hash = proof["transactions"][label]
    if not wait:
        return {"hash": tx_hash, "status": "SUBMITTED"}
    receipt = final(tx_hash, label, role=role, allow_error=allow_error)
    if not success(receipt):
        proof.setdefault("nonSuccessfulTransactions", {})[label] = {"status": receipt.get("status_name", receipt.get("status")), "result": receipt.get("result_name", "")}
        save_proof(proof)
    _follow_children(proof, label, receipt, role=role)
    return receipt


def read(address, method, args=None, role="TEAM_1"):
    result = client(role).read_contract(address, method, args=args or [], transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    return json.loads(result) if isinstance(result, str) and result.startswith(("{", "[")) else result
