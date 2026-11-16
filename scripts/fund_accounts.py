"""Fund the approved StudioNet poster and challenger signers."""

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from chain import ROOT, account, final, load_proof, save_proof, success

FUNDING_PATH = ROOT / "deploy/funding.json"
SOURCE = "moment-grid-studionet"
PLAN = [("team_1_demo_escrow", "TEAM_1", 200),
    ("challenger_1", "CHALLENGER_1", 20),
    ("challenger_2", "CHALLENGER_2", 10),
]
HASH_PATTERN = re.compile(r"0x[0-9a-fA-F]{64}")
APPROVED_TOTAL = 2000
PLANNED_GROSS = 890


def cli_command(*args):
    executable = shutil.which("genlayer.cmd") or shutil.which("genlayer")
    if not executable:
        raise RuntimeError("GenLayer CLI shim was not found on PATH")
    if executable.lower().endswith((".cmd", ".bat")):
        shell = shutil.which("cmd.exe") or "cmd.exe"
        return [shell, "/d", "/s", "/c", subprocess.list2cmdline([executable, *args])]
    return [executable, *args]


def save_funding(data):
    target = FUNDING_PATH.with_suffix(".tmp")
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    target.replace(FUNDING_PATH)


def run_transfer(label, role, amount, data, proof):
    recorded = data["transfers"].get(label)
    if recorded and recorded.get("transactionHash"):
        recipient = recorded["to"]
        tx_hash = recorded["transactionHash"]
        print(label, "resuming", tx_hash, flush=True)
    else:
        intent = ROOT / "deploy/.funding-intent.json"
        if intent.exists():
            previous = json.loads(intent.read_text(encoding="utf-8"))
            raise RuntimeError("Reconcile the saved funding intent before another transfer: " + previous.get("label", "unknown"))
        recipient = account(role).address
        intent.write_text(json.dumps({"label": label, "to": recipient, "wei": amount, "source": SOURCE}), encoding="utf-8")
        process = subprocess.Popen(
            cli_command("account", "send", recipient, str(amount), "--account", SOURCE),
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        if process.stdin:
            process.stdin.write("y\n")
            process.stdin.flush()
            process.stdin.close()
        tx_hash = None
        tail = []
        assert process.stdout is not None
        for line in process.stdout:
            tail.append(line.strip()[:240])
            tail = tail[-8:]
            if tx_hash is None:
                found = HASH_PATTERN.search(line)
                if found:
                    tx_hash = found.group(0)
                    data["transfers"][label] = {"to": recipient, "wei": amount, "transactionHash": tx_hash, "status": "SUBMITTED"}
                    proof["transactions"]["funding-" + label] = tx_hash
                    save_funding(data)
                    save_proof(proof)
                    print(label, "SUBMITTED", tx_hash, flush=True)
        exit_code = process.wait(timeout=300)
        if not tx_hash:
            intent.write_text(json.dumps({"label": label, "to": recipient, "wei": amount, "source": SOURCE, "outputTail": tail}), encoding="utf-8")
            raise RuntimeError("Funding command returned no transaction hash; saved a reconciliation intent")
        if exit_code != 0:
            print(label, "CLI exited", exit_code, "after recording the hash; resuming from the saved hash", flush=True)
        intent.unlink(missing_ok=True)
    receipt = final(tx_hash, "funding-" + label, attempts=360)
    if not success(receipt):
        raise RuntimeError("Funding transfer did not finalize successfully: " + label)
    data["transfers"][label]["status"] = "FINALIZED_SUCCESS"
    save_funding(data)


def main():
    data = json.loads(FUNDING_PATH.read_text(encoding="utf-8"))
    proof = load_proof()
    total = sum(amount for _, _, amount in PLAN)
    if int(data.get("approvedTotalWei", -1)) != APPROVED_TOTAL or total != int(data.get("plannedWei", {}).get("seedTransfers", -1)):
        raise RuntimeError("Funding manifest does not match the authorized seed-transfer schedule")
    if PLANNED_GROSS > APPROVED_TOTAL or int(data.get("plannedWei", {}).get("totalGross", -1)) != PLANNED_GROSS:
        raise RuntimeError("Total planned gross movement exceeds or differs from the authorized budget")
    for label, role, amount in PLAN:
        recipient = account(role).address
        data.setdefault("wallets", {})[label] = recipient
        save_funding(data)
        run_transfer(label, role, amount, data, proof)
    data["status"] = "FUNDED"
    save_funding(data)
    print("All three approved signer transfers are finalized; no private keys were printed.", flush=True)


if __name__ == "__main__":
    main()
