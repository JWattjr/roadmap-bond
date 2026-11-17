"""Audit local documentation links and final Portal evidence URLs."""

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests


ROOT = Path(__file__).resolve().parent.parent
PROOF_PATH = ROOT / "deploy/proof.json"
DOCS = [ROOT / "README.md", ROOT / "docs/tutorial.md", ROOT / "docs/demo-script.md", ROOT / "docs/portal.md"]
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
TX_HASH = re.compile(r"0x[0-9a-fA-F]{64}")
UA = {"User-Agent": "Mozilla/5.0 RoadmapBond-LinkAudit/1.0"}


def http_get(url, timeout=30):
    last_error = None
    for attempt in range(8):
        try:
            response = requests.get(url, headers=UA, timeout=timeout, allow_redirects=True)
        except requests.RequestException as error:
            last_error = error
            if attempt == 7:
                raise
        else:
            if response.status_code not in (429, 500, 502, 503, 504) or attempt == 7:
                response.raise_for_status()
                return response
        time.sleep(min(2 ** attempt, 30))
    raise RuntimeError("Explorer link retries exhausted for " + url) from last_error


def nested_address_objects(value):
    if isinstance(value, dict):
        if "type" in value and "address" in value:
            yield value
        for child in value.values():
            yield from nested_address_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_address_objects(child)


def audit_local_links():
    errors = []
    count = 0
    for document in DOCS:
        body = document.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(body):
            if target.startswith(("https://", "http://", "mailto:")):
                parsed = urlparse(target)
                if parsed.scheme in ("http", "https") and not parsed.netloc:
                    errors.append(str(document.relative_to(ROOT)) + ": malformed URL " + target)
                if parsed.netloc.lower() == "explorer-studio.genlayer.com":
                    if not re.fullmatch(r"/(?:address/0x[0-9a-fA-F]{40}|tx/0x[0-9a-fA-F]{64})", parsed.path):
                        errors.append(str(document.relative_to(ROOT)) + ": non-canonical StudioNet Explorer link " + target)
                count += 1
                continue
            path = unquote(target.split("#", 1)[0])
            if not path:
                continue
            resolved = (document.parent / path).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(str(document.relative_to(ROOT)) + ": link escapes the project: " + target)
                continue
            if not resolved.exists():
                errors.append(str(document.relative_to(ROOT)) + ": missing local link " + target)
            count += 1
    if errors:
        print("Local documentation links: FAIL")
        for error in errors:
            print("- " + error)
        return False
    print("Local documentation links: PASS (" + str(count) + " links)")
    return True


def audit_contract_urls(proof):
    contracts = proof.get("contracts", {})
    if set(contracts) != {"BondBoard", "PromiseJudge"}:
        print("Direct StudioNet Explorer links: BLOCKED (final contract addresses are missing)")
        return False
    for name, item in contracts.items():
        address = item.get("address", "")
        expected = proof.get("explorer", "").rstrip("/") + "/address/" + address
        direct = item.get("explorerUrl", "")
        if not ADDRESS.fullmatch(address) or direct != expected:
            print("Direct StudioNet Explorer links: FAIL (invalid address link for " + name + ")")
            return False
        try:
            api = http_get(proof.get("explorer", "").rstrip("/") + "/api/address/" + address)
            records = [obj for obj in nested_address_objects(api.json()) if str(obj.get("address", "")).lower() == address.lower()]
            if not any(obj.get("type") == "CONTRACT" for obj in records):
                print("Direct StudioNet Explorer links: FAIL (" + name + " address is not a contract record)")
                return False
            response = http_get(direct, timeout=20)
        except requests.RequestException as error:
            print("Direct StudioNet Explorer links: FAIL (" + name + ": " + str(error)[:180] + ")")
            return False
        except (ValueError, RuntimeError) as error:
            print("Direct StudioNet Explorer links: FAIL (" + name + ": " + str(error)[:180] + ")")
            return False
        if response.status_code != 200 or address.lower() not in response.url.lower():
            print("Direct StudioNet Explorer links: FAIL (" + name + " did not resolve to its address page)")
            return False
        print(name + ": PASS " + direct)
    for item in proof.get("retiredContracts", []):
        direct = item.get("explorerUrl")
        if not direct:
            continue
        address = item.get("address", "")
        expected = proof.get("explorer", "").rstrip("/") + "/address/" + address
        if not ADDRESS.fullmatch(address) or direct != expected:
            print("Retired contract Explorer links: FAIL (invalid address link for " + address + ")")
            return False
        try:
            api = http_get(proof.get("explorer", "").rstrip("/") + "/api/address/" + address)
            records = [obj for obj in nested_address_objects(api.json()) if str(obj.get("address", "")).lower() == address.lower()]
            if not any(obj.get("type") == "CONTRACT" for obj in records):
                print("Retired contract Explorer links: FAIL (" + address + " is not a contract record)")
                return False
            response = http_get(direct, timeout=20)
        except requests.RequestException as error:
            print("Retired contract Explorer links: FAIL (" + address + ": " + str(error)[:180] + ")")
            return False
        except (ValueError, RuntimeError) as error:
            print("Retired contract Explorer links: FAIL (" + address + ": " + str(error)[:180] + ")")
            return False
        if response.status_code != 200 or address.lower() not in response.url.lower():
            print("Retired contract Explorer links: FAIL (" + address + " did not resolve to its address page)")
            return False
        print("Retired contract address: PASS " + direct)
    return True


def audit_transaction_urls(proof):
    hashes = sorted(set(proof.get("transactions", {}).values()))
    if not hashes:
        print("Direct StudioNet Explorer transaction links: FAIL (no transaction hashes)")
        return False
    for tx_hash in hashes:
        if not TX_HASH.fullmatch(str(tx_hash)):
            print("Direct StudioNet Explorer transaction links: FAIL (malformed hash " + str(tx_hash) + ")")
            return False

    explorer = proof.get("explorer", "").rstrip("/")
    def check(tx_hash):
        url = explorer + "/tx/" + tx_hash
        response = http_get(url)
        parsed = urlparse(response.url)
        expected_path = "/tx/" + tx_hash
        if response.status_code != 200 or parsed.hostname != "explorer-studio.genlayer.com" or parsed.path.lower() != expected_path.lower():
            return tx_hash, False
        return tx_hash, True

    failures = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(check, tx_hash) for tx_hash in hashes]
        for future in as_completed(futures):
            try:
                tx_hash, ok = future.result()
            except requests.RequestException as error:
                failures.append(str(error)[:180])
                continue
            if not ok:
                failures.append(tx_hash)
    if failures:
        print("Direct StudioNet Explorer transaction links: FAIL (" + str(len(failures)) + " of " + str(len(hashes)) + ")")
        for failure in failures[:10]:
            print("- " + failure)
        return False
    print("Direct StudioNet Explorer transaction links: PASS (" + str(len(hashes)) + " transaction records)")
    return True


def main():
    proof = json.loads(PROOF_PATH.read_text(encoding="utf-8"))
    ok = audit_local_links()
    explorer_ok = audit_contract_urls(proof)
    transaction_links_ok = audit_transaction_urls(proof)
    if proof.get("chainId") != 61999:
        print("Explorer network: FAIL (expected StudioNet chain 61999)")
        ok = False
    elif explorer_ok:
        print("Explorer network: PASS (StudioNet chain 61999)")
    if not ok or not explorer_ok or not transaction_links_ok or proof.get("releaseStatus") != "LIVE_CASES_COMPLETE":
        print("Link audit: NOT COMPLETE; do not hand the Portal packet to a reviewer.")
        return 2
    print("Link audit: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
