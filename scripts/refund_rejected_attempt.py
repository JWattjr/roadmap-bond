"""Refund and archive a rejected live-case attempt before its corrected replay."""

from chain import load_proof, read, save_proof, tx


CASE_KEY = "rename_only"
PROMISE_ID = "promise-4"
REFUND_LABEL = "v2-refund-rejected-rename-only-promise-4"


def main():
    proof = load_proof()
    board = proof["contracts"]["BondBoard"]["address"]
    record = read(board, "get_promise", [PROMISE_ID])
    if not record or record.get("id") != PROMISE_ID:
        raise RuntimeError("The rejected v2 promise-4 attempt is missing")
    if record.get("status") == "REJECTED":
        tx(proof, REFUND_LABEL, board, "refund_rejected", [PROMISE_ID], role="TEAM_1")
    elif record.get("status") == "REJECT_REFUND_PENDING":
        if REFUND_LABEL not in proof.get("transactions", {}):
            raise RuntimeError("A rejected-promise refund is pending without its saved hash")
        tx(proof, REFUND_LABEL, board, "refund_rejected", [PROMISE_ID], role="TEAM_1")
    elif record.get("status") != "REJECTED_REFUNDED":
        raise RuntimeError("Unexpected rejected-attempt status: " + str(record.get("status")))

    record = read(board, "get_promise", [PROMISE_ID])
    if record.get("status") != "REJECTED_REFUNDED" or record.get("bond_wei") != "0":
        raise RuntimeError("Promise-4's rejected bond did not refund")

    refund_hashes = [
        (label, tx_hash)
        for label, tx_hash in proof.get("transactions", {}).items()
        if label.startswith(REFUND_LABEL)
    ]
    for action, tx_hash in refund_hashes:
        label = "v2-record-retired-promise-4-" + tx_hash[2:12]
        if label not in proof["transactions"]:
            tx(proof, label, board, "record_transaction", [PROMISE_ID, action[:80], tx_hash])

    attempts = proof.setdefault("caseAttempts", [])
    if not any(item.get("promiseId") == PROMISE_ID for item in attempts):
        attempts.append({
            "caseKey": CASE_KEY,
            "promiseId": PROMISE_ID,
            "promise": record,
            "compileReason": "The LLM compiler returned its safe rejection fallback for this long quote; the finalized callback did not fail consensus.",
            "disposition": "Bond refund finalized; the case will be replayed with a shorter verbatim quote under promise-5.",
            "refundTransaction": proof["transactions"][REFUND_LABEL],
        })
    save_proof(proof)
    print("Rejected promise-4 attempt refunded and archived; its 40-wei bond is released.", flush=True)


if __name__ == "__main__":
    main()
