"""Index and refresh preliminary v2 attempt refund evidence in the proof."""

from chain import load_proof, read, save_proof, tx


def main():
    proof = load_proof()
    board = next(
        (
            item["address"]
            for item in proof.get("retiredContracts", [])
            if item.get("release") == "v2" and item.get("name") == "BondBoard"
        ),
        None,
    )
    if not board:
        raise RuntimeError("The retired v2 BondBoard is not recorded in the proof")

    attempts = proof.get("caseAttempts", [])
    for attempt in attempts:
        promise_id = attempt.get("promiseId")
        if not promise_id:
            raise RuntimeError("A preliminary case attempt has no promise ID")
        promise = read(board, "get_promise", [promise_id])
        if not promise or promise.get("id") != promise_id:
            raise RuntimeError("The retired v2 promise is missing: " + promise_id)

        refund_hashes = attempt.get("refundTransactions", [])
        if not refund_hashes and attempt.get("refundTransaction"):
            refund_hashes = [attempt["refundTransaction"]]
        if any(tx_hash not in proof.get("transactions", {}).values() for tx_hash in refund_hashes):
            raise RuntimeError("A preliminary refund transaction is missing from the proof manifest")

        indexed = {item.get("hash") for item in promise.get("transactions", [])}
        for tx_hash in refund_hashes:
            if tx_hash in indexed:
                continue
            label = "v2-record-retired-attempt-" + promise_id + "-" + tx_hash[2:12]
            if label not in proof.get("transactions", {}):
                tx(
                    proof,
                    label,
                    board,
                    "record_transaction",
                    [promise_id, "preliminary-refund-" + tx_hash[2:18], tx_hash],
                )
            promise = read(board, "get_promise", [promise_id])
            indexed = {item.get("hash") for item in promise.get("transactions", [])}
            if tx_hash not in indexed:
                raise RuntimeError("Refund callback could not be indexed for " + promise_id)

        attempt["promise"] = promise
        print("REFRESHED", promise_id, promise.get("status"), len(indexed), "on-chain transactions", flush=True)

    save_proof(proof)
    print("Preliminary attempt snapshots now match retired v2 on-chain history.", flush=True)


if __name__ == "__main__":
    main()
