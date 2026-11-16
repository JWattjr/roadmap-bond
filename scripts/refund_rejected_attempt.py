"""Refund and archive a rejected live-case attempt before its corrected replay."""

import argparse

from chain import load_proof, read, save_proof, tx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-key", required=True)
    parser.add_argument("--promise-id", required=True)
    args = parser.parse_args()
    case_key = args.case_key
    promise_id = args.promise_id
    slug = case_key.replace("_", "-")
    refund_label = "v2-refund-rejected-" + slug + "-" + promise_id

    proof = load_proof()
    board = proof["contracts"]["BondBoard"]["address"]
    record = read(board, "get_promise", [promise_id])
    if not record or record.get("id") != promise_id:
        raise RuntimeError("The rejected v2 attempt is missing: " + promise_id)
    if record.get("status") == "REJECTED":
        tx(proof, refund_label, board, "refund_rejected", [promise_id], role="TEAM_1")
    elif record.get("status") == "REJECT_REFUND_PENDING":
        if refund_label not in proof.get("transactions", {}):
            raise RuntimeError("A rejected-promise refund is pending without its saved hash")
        tx(proof, refund_label, board, "refund_rejected", [promise_id], role="TEAM_1")
    elif record.get("status") != "REJECTED_REFUNDED":
        raise RuntimeError("Unexpected rejected-attempt status: " + str(record.get("status")))

    record = read(board, "get_promise", [promise_id])
    if record.get("status") != "REJECTED_REFUNDED" or record.get("bond_wei") != "0":
        raise RuntimeError("Promise-4's rejected bond did not refund")

    refund_hashes = [
        (label, tx_hash)
        for label, tx_hash in proof.get("transactions", {}).items()
        if label.startswith(refund_label)
    ]
    for action, tx_hash in refund_hashes:
        label = "v2-record-retired-" + slug + "-" + promise_id + "-" + tx_hash[2:12]
        if label not in proof["transactions"]:
            tx(proof, label, board, "record_transaction", [promise_id, action[:80], tx_hash])

    attempts = proof.setdefault("caseAttempts", [])
    if not any(item.get("promiseId") == promise_id for item in attempts):
        attempts.append({
            "caseKey": case_key,
            "promiseId": promise_id,
            "promise": record,
            "compileReason": record.get("reason", "Compiler classified the quote as too broad for a frozen observable criterion."),
            "disposition": "Bond refund finalized; the intended case is retried with its corrected quote under the next ID in deploy/cases.json.",
            "refundTransaction": proof["transactions"][refund_label],
        })
    save_proof(proof)
    print("Rejected attempt", promise_id, "refunded and archived; its 40-wei bond is released.", flush=True)


if __name__ == "__main__":
    main()
