"""Finish, archive, and drain the v3 demonstration pair before v4."""

import time

import release
from chain import client, load_proof, read, save_proof, tx


V3_BOARD = "0xBf3C8BA4e2f21ac9a8cF2D91F527299AE40Fd068"
V3_JUDGE = "0x6b2703a021D92fce49D6F63387b795eA881346A2"
FINISH_CASES = ("spec_rejected", "kept", "broken", "rename_only", "injection", "unchallenged")
TERMINAL = {"REJECTED_REFUNDED", "KEPT", "BROKEN", "UNPROVEN", "RELEASED"}


def wait_until(timestamp, label):
    while int(time.time()) < int(timestamp):
        remaining = int(timestamp) - int(time.time())
        print(label, "opens in", remaining, "seconds", flush=True)
        time.sleep(min(10, max(1, remaining)))


def save_retired(proof, key, record):
    rows = proof.setdefault("retiredCaseResults", [])
    item = next((row for row in rows if row.get("release") == "v3" and row.get("promiseId") == record["id"]), None)
    if item is None:
        item = {"release": "v3", "caseKey": key, "promiseId": record["id"]}
        rows.append(item)
    item["promise"] = record
    item["retirementLabels"] = sorted(
        label for label in proof.get("transactions", {})
        if label.startswith("v3retire-") and (key in label or record["id"] in label)
    )
    if key == "unproven" and record.get("status") == "KEPT":
        item["disposition"] = "Finalized false positive: evidence repeated the future codemod promise but did not establish publication. Replaced by v4's deterministic promise-echo guard."
    if key == "rename_only" and record.get("status") == "KEPT":
        item["disposition"] = "Finalized false positive: evidence showed next build --turbopack only in alpha; the frozen rule excludes experimental states. Replaced by v4's deterministic excluded-state guard."
    save_proof(proof)


def assert_terminal(record):
    if record.get("status") not in TERMINAL:
        raise RuntimeError(record.get("id", "promise") + " is not terminal: " + str(record.get("status")))
    if record.get("bond_wei") != "0" or record.get("challenge_stake_wei") != "0":
        raise RuntimeError(record.get("id", "promise") + " still holds bond or stake")
    if any(payout.get("state") != "FINALIZED" for payout in record.get("payouts", [])):
        raise RuntimeError(record.get("id", "promise") + " has a nonfinal payout")


def main():
    proof = load_proof()
    contracts = proof.get("contracts", {})
    if contracts.get("BondBoard", {}).get("address", "").lower() != V3_BOARD.lower():
        raise RuntimeError("The recorded active BondBoard is not the v3 pair being retired")
    if contracts.get("PromiseJudge", {}).get("address", "").lower() != V3_JUDGE.lower():
        raise RuntimeError("The recorded active PromiseJudge is not the v3 pair being retired")
    cases = release.load_cases(proof)
    release.CASE_TAG = "v3retire"
    board = V3_BOARD

    for key in FINISH_CASES:
        promise_id = cases[key]["promiseId"]
        record = read(board, "get_promise", [promise_id])
        if not record or record.get("id") != promise_id:
            raise RuntimeError("Missing v3 promise " + promise_id)
        if record.get("status") not in TERMINAL:
            try:
                release._run_case(proof, key, cases[key], finish_only=True)
            except RuntimeError as error:
                record = read(board, "get_promise", [promise_id])
                if record.get("status") not in TERMINAL:
                    if record.get("status") == "OPEN":
                        wait_until(int(record.get("challenge_close_at", 0)), "v3 " + promise_id + " release")
                        label = "v3retire-release-" + promise_id
                        tx(proof, label, board, "release", [promise_id])
                    else:
                        grace_end = int(record.get("defence_end", 0)) + int(record.get("grace_seconds", 0))
                        wait_until(grace_end, "v3 " + promise_id + " grace refund")
                        label = "v3retire-expired-" + promise_id
                        tx(proof, label, board, "settle_expired", [promise_id])
                    record = read(board, "get_promise", [promise_id])
                elif record.get("status") == cases[key]["expectedStatus"]:
                    print(key, "settled after resumable runner reported:", str(error)[:160], flush=True)
                else:
                    print(key, "finalized as", record.get("status"), "during retirement", flush=True)
        record = read(board, "get_promise", [promise_id])
        assert_terminal(record)
        proof.setdefault("cases", {}).setdefault(key, {}).update({"promise": record, "finalStatus": record["status"]})
        save_retired(proof, key, record)
        print(key, record["status"], "finalized and empty", flush=True)

    # Archive the already-final v3 false positive without presenting it as a valid final outcome.
    unproven_id = cases["unproven"]["promiseId"]
    unproven = read(board, "get_promise", [unproven_id])
    assert_terminal(unproven)
    save_retired(proof, "unproven", unproven)

    balances = read(board, "get_balances", [cases["spec_rejected"]["promiseId"]])
    if int(balances.get("contract_balance_wei", "-1")) != 0:
        raise RuntimeError("The v3 Board still holds " + str(balances.get("contract_balance_wei")) + " wei in escrow")
    for name, item in contracts.items():
        result = client().provider.make_request("eth_getBalance", [item["address"], "latest"])
        value = result.get("result") if isinstance(result, dict) else result
        if not isinstance(value, str) or int(value, 16) != 0:
            raise RuntimeError("The v3 " + name + " native balance is not zero")

    source_commit = proof.get("sourceCommit", "")
    retired = proof.setdefault("retiredContracts", [])
    for name, item in contracts.items():
        if not any(row.get("address", "").lower() == item["address"].lower() for row in retired):
            retired.append({
                **item,
                "name": name,
                "release": "v3",
                "internalBalanceWei": "0" if name == "BondBoard" else None,
                "retiredReason": "Replaced after the finalized promise-echo false positive; all seven v3 promises are settled and escrow is zero.",
            })
    commits = proof.setdefault("retiredReleaseCommits", [])
    if source_commit and not any(row.get("release") == "v3" for row in commits):
        commits.append({"release": "v3", "sourceCommit": source_commit})

    proof["contracts"] = {}
    proof["cases"] = {}
    proof["releaseStatus"] = "V3_RETIRED"
    save_proof(proof)
    print("v3 pair retired; all case payouts are final and Board escrow and both native balances are zero.", flush=True)


if __name__ == "__main__":
    main()
