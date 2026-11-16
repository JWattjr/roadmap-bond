"""Refund the canceled v1 compile and prove its contracts hold no funds."""

import json
import time

from chain import ROOT, client, load_proof, read, save_proof, tx


OLD_CASE_LABEL = "post-spec_rejected-child-0"
REFUND_LABEL = "v1-refund_compile_expired-promise-1"
PROMISE_ID = "promise-1"


def eth_balance(address):
    response = client().provider.make_request("eth_getBalance", [address, "latest"])
    value = response.get("result") if isinstance(response, dict) else None
    if not isinstance(value, str) or not value.startswith("0x"):
        raise RuntimeError("Could not read the retired contract native balance")
    return int(value, 16)


def main():
    proof = load_proof()
    contracts = proof.get("contracts", {})
    if set(contracts) != {"BondBoard", "PromiseJudge"}:
        raise RuntimeError("The failed release's two contracts are not recorded")
    board = contracts["BondBoard"]["address"]
    receipt_path = ROOT / "deploy/receipts" / (OLD_CASE_LABEL + ".json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    tx_hash = proof.get("transactions", {}).get(OLD_CASE_LABEL)
    if receipt.get("tx_id", "").lower() != str(tx_hash).lower():
        raise RuntimeError("Canceled compile receipt does not match the saved transaction hash")
    if receipt.get("result_name") != "NO_MAJORITY" or (receipt.get("consensus_data") or {}).get("error") != "max_recovery_cycles_exceeded":
        raise RuntimeError("The v1 compile failure receipt does not match the diagnosed consensus failure")

    record = read(board, "get_promise", [PROMISE_ID])
    if not record or record.get("id") != PROMISE_ID:
        raise RuntimeError("The v1 promise-1 escrow record is missing")
    if record.get("status") == "COMPILING":
        expires_at = int(record.get("created_at", 0)) + int(record.get("grace_seconds", 1800)) + 30
        while int(time.time()) < expires_at:
            remaining = expires_at - int(time.time())
            print("v1 refund window opens in", remaining, "seconds", flush=True)
            time.sleep(min(10, max(1, remaining)))
        tx(proof, REFUND_LABEL, board, "refund_compile_expired", [PROMISE_ID], role="TEAM_1")
    elif record.get("status") == "REFUNDABLE_ERROR":
        if REFUND_LABEL not in proof.get("transactions", {}):
            raise RuntimeError("Refund callback is pending but its transaction hash is not recorded")
        tx(proof, REFUND_LABEL, board, "refund_compile_expired", [PROMISE_ID], role="TEAM_1")
    elif record.get("status") != "REFUNDED_INVALID":
        raise RuntimeError("Unexpected v1 promise status before retirement: " + str(record.get("status")))

    record = read(board, "get_promise", [PROMISE_ID])
    balances = read(board, "get_balances", [PROMISE_ID])
    if record.get("status") != "REFUNDED_INVALID" or balances.get("bond_held_wei") != "0":
        raise RuntimeError("The failed v1 bond did not finalize its invalid-promise refund")

    retired = proof.setdefault("retiredContracts", [])
    retired_items = [(name, item) for name, item in contracts.items()]
    retired_items.extend(("AccessProbe-v1", item) for item in proof.get("retiredProbeContracts", []))
    retired_items.extend(("AccessProbe-v2", item) for item in proof.get("probeContracts", {}).values())
    for name, item in retired_items:
        balance = eth_balance(item["address"])
        if balance != 0:
            raise RuntimeError(name + " still holds " + str(balance) + " wei after retirement")
        entry = dict(item)
        entry["retiredReason"] = (
            "v1 compile callback canceled with NO_MAJORITY; v2 replaces this pair after deterministic validation."
            if name in contracts else "Pre-release validator access probe; not part of the final product pair."
        )
        entry["balanceWei"] = "0"
        entry["retiredStatus"] = "REFUNDED_AND_DRAINED" if name == "BondBoard" else "DRAINED"
        if not any(old.get("address", "").lower() == item["address"].lower() for old in retired):
            retired.append(entry)

    proof.setdefault("nonSuccessfulTransactions", {})[OLD_CASE_LABEL] = {
        "status": "CANCELED",
        "result": "NO_MAJORITY",
        "reason": "max_recovery_cycles_exceeded",
        "disposition": "Retired v1 compile callback; its promise escrow was refunded and both v1 contracts were drained.",
    }
    proof["retiredReleaseSourceCommit"] = proof.get("sourceCommit", "")
    proof["contracts"] = {}
    proof["cases"] = {}
    proof["releaseStatus"] = "RETRY_REQUIRED"
    save_proof(proof)
    print("v1 contracts retired; promise-1 refunded; both native contract balances are zero.", flush=True)


if __name__ == "__main__":
    main()
