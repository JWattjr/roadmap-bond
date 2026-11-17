"""Finalize or grace-refund v2 promises, then retire the funded v2 pair."""

import time

from chain import client, load_proof, read, save_proof, tx


V2_CASES = [
    ("broken", "promise-3"),
    ("rename_only", "promise-5"),
    ("injection", "promise-8"),
    ("unchallenged", "promise-9"),
    ("unproven", "promise-10"),
]
TERMINAL = {"KEPT", "BROKEN", "UNPROVEN", "RELEASED", "REJECTED_REFUNDED"}


def wait_until(timestamp, label):
    while int(time.time()) < int(timestamp):
        remaining = int(timestamp) - int(time.time())
        print(label, "opens in", remaining, "seconds", flush=True)
        time.sleep(min(10, max(1, remaining)))


def assert_settled(record):
    if record.get("status") not in TERMINAL:
        raise RuntimeError(record.get("id", "promise") + " has nonterminal status " + str(record.get("status")))
    if record.get("bond_wei") != "0" or record.get("challenge_stake_wei") != "0":
        raise RuntimeError(record.get("id", "promise") + " still holds bond or challenge stake")
    if any(item.get("state") != "FINALIZED" for item in record.get("payouts", [])):
        raise RuntimeError(record.get("id", "promise") + " has a nonfinal payout")


def save_retired_case(proof, key, record, retirement_labels=None):
    rows = proof.setdefault("retiredCaseResults", [])
    item = next((row for row in rows if row.get("promiseId") == record["id"]), None)
    if item is None:
        item = {"release": "v2", "caseKey": key, "promiseId": record["id"]}
        rows.append(item)
    item["promise"] = record
    if retirement_labels:
        item["retirementLabels"] = sorted(set(item.get("retirementLabels", [])) | set(retirement_labels))
    proof.setdefault("cases", {}).setdefault(key, {}).update({"promise": record, "finalStatus": record["status"]})
    save_proof(proof)


def main():
    proof = load_proof()
    if set(proof.get("contracts", {})) != {"BondBoard", "PromiseJudge"}:
        raise RuntimeError("The recorded active pair is not the v2 BondBoard and PromiseJudge pair")
    board = proof["contracts"]["BondBoard"]["address"]

    for key, promise_id in V2_CASES:
        record = read(board, "get_promise", [promise_id])
        if not record or record.get("id") != promise_id:
            raise RuntimeError("Missing v2 promise " + promise_id)
        if record.get("status") in TERMINAL:
            assert_settled(record)
            save_retired_case(proof, key, record)
            print(key, record["status"], "already finalized", flush=True)
            continue
        if key == "unchallenged":
            if record.get("status") != "OPEN":
                raise RuntimeError("Unexpected v2 unchallenged state: " + str(record.get("status")))
            wait_until(int(record.get("challenge_close_at", 0)), "v2 " + promise_id + " release")
            before = set(proof.get("transactions", {}))
            tx(proof, "v2retire-release-" + promise_id, board, "release", [promise_id])
        else:
            if record.get("status") not in ("CHALLENGED", "READY_TO_JUDGE", "JUDGING"):
                raise RuntimeError("Unexpected v2 challenged state for " + promise_id + ": " + str(record.get("status")))
            grace_end = int(record.get("defence_end", 0)) + int(record.get("grace_seconds", 0))
            wait_until(grace_end, "v2 " + promise_id + " grace refund")
            before = set(proof.get("transactions", {}))
            tx(proof, "v2retire-expired-" + promise_id, board, "settle_expired", [promise_id])
        retirement_labels = [label for label in proof.get("transactions", {}) if label not in before]
        record = read(board, "get_promise", [promise_id])
        assert_settled(record)
        save_retired_case(proof, key, record, retirement_labels)
        print(key, record["status"], "finalized and empty", flush=True)

    # Preserve every v2 case record, including the already-final rejected case.
    for key, item in proof.get("cases", {}).items():
        record = item.get("promise", {})
        if record.get("id") and record.get("status") in TERMINAL:
            assert_settled(record)
            save_retired_case(proof, key, record)

    internal = read(board, "get_balances", ["promise-3"])
    if int(internal.get("contract_balance_wei", "-1")) != 0:
        raise RuntimeError("The v2 Board still holds " + str(internal.get("contract_balance_wei")) + " wei in escrow")
    for name, item in proof["contracts"].items():
        result = client().provider.make_request("eth_getBalance", [item["address"], "latest"])
        value = result.get("result") if isinstance(result, dict) else result
        if not isinstance(value, str) or int(value, 16) != 0:
            raise RuntimeError("The v2 " + name + " native balance is not zero")

    source_commit = proof.get("sourceCommit", "")
    retired = proof.setdefault("retiredContracts", [])
    for name, item in proof["contracts"].items():
        if not any(row.get("address", "").lower() == item["address"].lower() for row in retired):
            retired.append({**item, "name": name, "release": "v2", "internalBalanceWei": "0" if name == "BondBoard" else None, "retiredReason": "Repeated finalized LLM_ERROR on the positive judge case; all v2 promise funds were settled or refunded."})
    commits = proof.setdefault("retiredReleaseCommits", [])
    if source_commit and not any(row.get("release") == "v2" for row in commits):
        commits.append({"release": "v2", "sourceCommit": source_commit})

    proof["contracts"] = {}
    proof["cases"] = {}
    proof["releaseStatus"] = "V2_RETIRED"
    save_proof(proof)
    print("v2 pair retired; Board escrow and both native contract balances are zero.", flush=True)


if __name__ == "__main__":
    main()
