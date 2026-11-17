"""Resumable final-contract deployment and historical promise replays."""

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

from chain import ROOT, account, client, load_proof, read, save_proof, tx


CASE_FILE = ROOT / "deploy/cases.json"
WINDOW_SECONDS = 1800
BOND_WEI = 40
EXPLORER = "https://explorer-studio.genlayer.com"
RELEASE_TAG = "v2"
CASE_TAG = os.environ.get("CASE_TAG", "v2d")
REQUIRED_CASES = {
    "spec_rejected": "REJECTED_REFUNDED",
    "kept": "KEPT",
    "broken": "BROKEN",
    "rename_only": "BROKEN",
    "injection": "UNPROVEN",
    "unchallenged": "RELEASED",
    "unproven": "UNPROVEN",
}
REQUIRED_LABELS = {"SPEC_REJECTED", "KEPT", "BROKEN", "RENAME_ONLY", "INJECTION", "UNPROVEN", "UNCHALLENGED"}


def save(proof):
    save_proof(proof)


def address(proof, name):
    return proof["contracts"][name]["address"]


def git_revision():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        encoding="utf-8", capture_output=True, check=False,
    )
    if result.returncode or not re.fullmatch(r"[0-9a-f]{40}", result.stdout.strip()):
        raise RuntimeError("Commit the reviewed source before deployment; sourceCommit must be a Git SHA.")
    return result.stdout.strip()


def chain_id():
    result = client().provider.make_request("eth_chainId", [])
    value = result.get("result") if isinstance(result, dict) else result
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    return int(value)


def _probe_flags(proof):
    results = proof.get("probeResults", {}).get("results", [])
    rows = {row.get("source"): row for row in results}
    wayback = all(rows.get(name, {}).get("reachable") is True for name in ("wayback_cdx", "wayback_id_snapshot"))
    return {
        "allow_wayback": wayback,
        "allow_github_raw": rows.get("github_raw", {}).get("reachable") is True,
        "allow_npm": rows.get("npm_exact_version", {}).get("reachable") is True,
        "allow_wikipedia": rows.get("wikipedia_oldid", {}).get("reachable") is True,
    }


def load_cases(proof):
    if not CASE_FILE.exists():
        raise RuntimeError("Missing deploy/cases.json; verified historical replay inputs are required before release.")
    data = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    if data.get("status") != "READY":
        raise RuntimeError("Historical replay source verification is incomplete; deploy/cases.json is not READY.")
    cases = data.get("cases", {})
    if set(cases) != set(REQUIRED_CASES):
        raise RuntimeError("deploy/cases.json must define exactly the seven required replay cases.")
    now = int(time.time())
    labels = set()
    promise_ids = [item.get("promiseId") for item in cases.values()]
    if len(set(promise_ids)) != len(REQUIRED_CASES) or any(not re.fullmatch(r"promise-[1-9][0-9]*", str(value)) for value in promise_ids):
        raise RuntimeError("Each replay case must use a unique positive promise ID from deploy/cases.json.")
    for key, expected in REQUIRED_CASES.items():
        item = cases[key]
        labels.update(item.get("labels", []))
        if item.get("expectedStatus") != expected or item.get("bondWei") != BOND_WEI:
            raise RuntimeError("Unexpected case outcome or bond amount for " + key)
        quote = item.get("quote")
        snapshot = item.get("snapshotUrl")
        deadline = item.get("deadline")
        if not isinstance(quote, str) or not 20 <= len(quote) <= 300:
            raise RuntimeError("A verbatim 20-300 character quote is missing for " + key)
        if not isinstance(snapshot, str) or not re.fullmatch(r"https://web\.archive\.org/web/\d{14}id_/https://.+", snapshot):
            raise RuntimeError("An exact Wayback id_ snapshot URL is missing for " + key)
        if not isinstance(deadline, int) or deadline >= now:
            raise RuntimeError("A past historical deadline is missing for " + key)
        if key == "spec_rejected" or key == "unchallenged":
            if item.get("challenge") is not None:
                raise RuntimeError(key + " must be unchallenged in the case manifest")
        else:
            challenge = item.get("challenge")
            if not isinstance(challenge, dict):
                raise RuntimeError("Challenge inputs are missing for " + key)
            if challenge.get("stakeWei") != BOND_WEI // 4:
                raise RuntimeError("Challenge stake must be exactly one quarter of the bond for " + key)
            evidence = challenge.get("evidenceUrls")
            if not isinstance(evidence, list) or not 1 <= len(evidence) <= 3:
                raise RuntimeError("One to three evidence URLs are required for " + key)
            if not re.fullmatch(r"TEAM_[1-5]", item.get("posterRole", "")):
                raise RuntimeError("A funded team poster role is required for " + key)
            if not re.fullmatch(r"CHALLENGER_[12]", challenge.get("role", "")):
                raise RuntimeError("A funded challenger role is required for " + key)
            for row in evidence:
                if not isinstance(row, str) or not row.startswith("https://"):
                    raise RuntimeError("Evidence URLs must use HTTPS for " + key)
        if key == "injection":
            commit = item.get("fixtureCommitSha", "")
            if not re.fullmatch(r"[0-9a-f]{40}", commit):
                raise RuntimeError("The injection fixture must be pinned to a full commit SHA.")
            fixture_url = "https://raw.githubusercontent.com/JWattjr/bounty-bench-fixtures/" + commit + "/roadmap-bond/evidence/ai-injection.txt"
            if fixture_url not in item["challenge"]["evidenceUrls"]:
                raise RuntimeError("The injection challenge must use the SHA-pinned public fixture file.")
        if not re.fullmatch(r"TEAM_[1-5]", item.get("posterRole", "")):
            raise RuntimeError("A funded team poster role is required for " + key)
    if labels != REQUIRED_LABELS:
        raise RuntimeError("Replay labels must cover every required case type exactly; missing: " + ", ".join(sorted(REQUIRED_LABELS - labels)))
    if proof.get("approvedTotalWei", 0) < 2000:
        raise RuntimeError("Proof manifest is missing the approved StudioNet wei budget.")
    return cases


def require_probe(proof):
    if not proof.get("probeContracts", {}).get("AccessProbe", {}).get("address"):
        raise RuntimeError("The AccessProbe must finalize before final-contract deployment.")
    results = proof.get("probeResults", {}).get("results", [])
    if not results:
        raise RuntimeError("The five-source validator probe has no finalized results.")
    flags = _probe_flags(proof)
    if not flags["allow_wayback"]:
        raise RuntimeError("Validators could not confirm both Wayback CDX and id_ access; snapshot posting cannot proceed.")
    if not any(flags[name] for name in ("allow_github_raw", "allow_npm", "allow_wikipedia")):
        raise RuntimeError("No immutable challenge evidence source passed the validator probe.")
    return flags


def deploy_contracts(proof, flags, revision):
    proof.setdefault("contracts", {})
    board_path = ROOT / "contracts/bond_board.py"
    judge_path = ROOT / "contracts/promise_judge.py"
    board_source = board_path.read_text(encoding="utf-8")
    judge_source = judge_path.read_text(encoding="utf-8")
    specs = [
        ("BondBoard", board_path, board_source, [WINDOW_SECONDS, WINDOW_SECONDS, WINDOW_SECONDS,
         flags["allow_wayback"], flags["allow_github_raw"], flags["allow_npm"], flags["allow_wikipedia"]]),
        ("PromiseJudge", judge_path, judge_source, None),
    ]
    for name, source_path, source, args in specs:
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        current = proof["contracts"].get(name)
        if current:
            if current.get("sha256") != digest:
                raise RuntimeError(name + " source hash differs from the deployed contract.")
            continue
        deploy_args = args if args is not None else [address(proof, "BondBoard")]
        receipt = tx(proof, RELEASE_TAG + "-deploy-" + name, code=source, args=deploy_args)
        deployed = receipt.get("recipient", receipt.get("to_address"))
        if not isinstance(deployed, str) or not re.fullmatch(r"0x[0-9a-fA-F]{40}", deployed):
            raise RuntimeError(name + " deployment finalized without a contract address.")
        proof["contracts"][name] = {
            "address": deployed,
            "source": source_path.name,
            "sha256": digest,
            "explorerUrl": EXPLORER + "/address/" + deployed,
        }
        save(proof)
    configure_label = RELEASE_TAG + "-configure-promise-judge"
    if configure_label not in proof["transactions"]:
        tx(proof, configure_label, address(proof, "BondBoard"), "set_promise_judge", [address(proof, "PromiseJudge")])
    proof["sourceCommit"] = revision
    proof["releaseStatus"] = "CONTRACTS_DEPLOYED"
    save(proof)


def _wait_until(timestamp, label):
    while int(time.time()) < int(timestamp):
        remaining = int(timestamp) - int(time.time())
        print(label, "opens in", remaining, "seconds", flush=True)
        time.sleep(min(10, max(1, remaining)))


def _record_hashes(proof, case_key, promise_id, before):
    board = address(proof, "BondBoard")
    current = proof["transactions"]
    case_record = proof.setdefault("cases", {}).setdefault(case_key, {})
    recorded = case_record.setdefault("recordedLabels", [])
    prefixes = tuple(CASE_TAG + "-" + action + case_key for action in ("post-", "challenge-", "judge-", "refund-", "release-", "defend-"))
    candidates = [name for name in current if name not in recorded and name.startswith(prefixes)]
    for tx_label in candidates:
        record_label = CASE_TAG + "-record-" + case_key + "-" + hashlib.sha256(tx_label.encode("utf-8")).hexdigest()[:10]
        if record_label not in proof["transactions"]:
            tx(proof, record_label, board, "record_transaction", [promise_id, tx_label[:80], current[tx_label]])
        recorded.append(tx_label)
        save(proof)


def _read_case(proof, item):
    return read(address(proof, "BondBoard"), "get_promise", [item["promiseId"]])


def _sync_case(proof, key, item):
    stored = _read_case(proof, item)
    if not stored or not stored.get("id"):
        raise RuntimeError("Promise record is missing for " + key)
    proof.setdefault("cases", {}).setdefault(key, {}).update({"promise": stored, "finalStatus": stored.get("status", "")})
    save(proof)
    return stored


def _wait_for_compilation(proof, key, item):
    for _ in range(360):
        record = _sync_case(proof, key, item)
        if record.get("status") != "COMPILING":
            return record
        time.sleep(10)
    raise RuntimeError("Criteria compilation is still pending for " + key)


def _run_case(proof, key, item, stage_only=False, finish_only=False):
    board = address(proof, "BondBoard")
    promise_id = item["promiseId"]
    if finish_only:
        record = _sync_case(proof, key, item)
    else:
        existing = proof.get("cases", {}).get(key, {}).get("promise")
        if not isinstance(existing, dict) or existing.get("id") != promise_id:
            proof.setdefault("cases", {})[key] = {"recordedLabels": []}
            before = set(proof["transactions"])
            tx(proof, CASE_TAG + "-post-" + key, board, "post_replay", [item["snapshotUrl"], item["quote"], item["deadline"], account(item["posterRole"]).address], value=BOND_WEI)
            _record_hashes(proof, key, promise_id, before)
        record = _wait_for_compilation(proof, key, item)

    expected = item["expectedStatus"]
    if record.get("status") == expected:
        proof.setdefault("cases", {}).setdefault(key, {}).update({"promise": record, "finalStatus": expected, "replay": True})
        save(proof)
        return record
    if record.get("status") == "REFUNDABLE_ERROR":
        raise RuntimeError("Snapshot or compile check failed for " + key + ": " + str(record.get("reason", "")))

    if key == "spec_rejected":
        if record.get("status") == "REJECTED":
            before = set(proof["transactions"])
            tx(proof, CASE_TAG + "-refund-" + key, board, "refund_rejected", [promise_id], role=item["posterRole"])
            _record_hashes(proof, key, promise_id, before)
        record = _sync_case(proof, key, item)
    elif key == "unchallenged":
        if stage_only:
            print(key, "STAGED", record.get("status"), flush=True)
            return record
        _wait_until(int(record.get("challenge_close_at", 0)), key + " release")
        before = set(proof["transactions"])
        tx(proof, CASE_TAG + "-release-" + key, board, "release", [promise_id])
        _record_hashes(proof, key, promise_id, before)
        record = _sync_case(proof, key, item)
    else:
        challenge = item["challenge"]
        if not finish_only and record.get("status") == "OPEN":
            before = set(proof["transactions"])
            result = tx(proof, CASE_TAG + "-challenge-" + key, board, "challenge", [promise_id, json.dumps(challenge["evidenceUrls"], separators=(",", ":"))], role=challenge["role"], value=challenge["stakeWei"])
            _record_hashes(proof, key, promise_id, before)
            if result.get("status_name") == "FINALIZED_ERROR":
                raise RuntimeError("Challenge transaction failed for " + key)
        record = _sync_case(proof, key, item)
        if record.get("status") == "CHALLENGED" and not finish_only:
            defence = item.get("defenceEvidenceUrls", [])
            if defence and not record.get("defence_evidence"):
                before = set(proof["transactions"])
                tx(proof, CASE_TAG + "-defend-" + key, board, "defend", [promise_id, json.dumps(defence, separators=(",", ":"))], role=item["posterRole"])
                _record_hashes(proof, key, promise_id, before)
                record = _sync_case(proof, key, item)
        if stage_only:
            if record.get("status") not in ("CHALLENGED", "READY_TO_JUDGE", "JUDGING", "RESULT_PENDING"):
                raise RuntimeError("Challenge was not accepted for " + key + ": " + str(record.get("status")))
            print(key, "STAGED", record.get("status"), flush=True)
            return record
        if record.get("status") not in ("CHALLENGED", "READY_TO_JUDGE", "JUDGING", "RESULT_PENDING"):
            raise RuntimeError("Challenge was not accepted for " + key + ": " + str(record.get("status")))
        _wait_until(int(record.get("defence_end", 0)), key + " judging")
        if record.get("status") in ("JUDGING", "RESULT_PENDING"):
            pending_index = int(record.get("next_criterion", 0))
            if record.get("status") == "RESULT_PENDING":
                pending_index -= 1
            pending_label = CASE_TAG + "-judge-" + key + "-" + str(pending_index)
            if pending_index >= 0 and pending_label in proof["transactions"]:
                tx(proof, pending_label, board, "judge_next", [promise_id])
        for _ in range(3):
            record = _sync_case(proof, key, item)
            if record.get("status") in ("KEPT", "BROKEN", "UNPROVEN"):
                break
            if record.get("status") == "JUDGING":
                elapsed = int(record.get("defence_end", 0)) + WINDOW_SECONDS - int(time.time())
                if elapsed <= 0:
                    raise RuntimeError("A judge callback is still pending for " + key + "; resume after finality.")
                time.sleep(min(10, elapsed))
                continue
            if record.get("status") not in ("CHALLENGED", "READY_TO_JUDGE"):
                break
            index = int(record.get("next_criterion", 0))
            before = set(proof["transactions"])
            tx(proof, CASE_TAG + "-judge-" + key + "-" + str(index), board, "judge_next", [promise_id])
            _record_hashes(proof, key, promise_id, before)
        record = _sync_case(proof, key, item)

    if record.get("status") != expected:
        raise RuntimeError(key + " finalized " + str(record.get("status")) + "; expected " + expected)
    proof["cases"][key].update({"promise": record, "finalStatus": record["status"], "replay": True})
    save(proof)
    print(key, record["status"], "FINALIZED", flush=True)
    return record


def run_cases(proof, cases):
    for key in REQUIRED_CASES:
        _run_case(proof, key, cases[key], stage_only=True)
    windows = []
    for key, item in cases.items():
        record = _sync_case(proof, key, item)
        if record.get("status") == item["expectedStatus"]:
            continue
        if key == "unchallenged":
            windows.append(int(record.get("challenge_close_at", 0)))
        elif record.get("status") in ("CHALLENGED", "READY_TO_JUDGE", "JUDGING", "RESULT_PENDING"):
            windows.append(int(record.get("defence_end", 0)))
    if windows:
        _wait_until(max(windows), "All historical replay windows")
    for key in ("kept", "injection", "unproven", "broken", "rename_only", "unchallenged"):
        _run_case(proof, key, cases[key], finish_only=True)
    proof["releaseStatus"] = "LIVE_CASES_COMPLETE"
    save(proof)


def main():
    proof = load_proof()
    if int(proof.get("chainId", 0)) != 61999 or chain_id() != 61999:
        raise RuntimeError("Connected RPC is not StudioNet chain 61999.")
    if not proof.get("probeResults", {}).get("results"):
        raise RuntimeError("Run scripts/probe.py and verify its finalized results before release.")
    flags = require_probe(proof)
    cases = load_cases(proof)
    revision = git_revision()
    deploy_contracts(proof, flags, revision)
    run_cases(proof, cases)
    print("All seven historical cases finalized on StudioNet; Explorer links are in deploy/proof.json.", flush=True)


if __name__ == "__main__":
    main()
