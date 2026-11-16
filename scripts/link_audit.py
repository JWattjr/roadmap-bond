"""Audit local documentation links and final Portal evidence URLs."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests


ROOT = Path(__file__).resolve().parent.parent
PROOF_PATH = ROOT / "deploy/proof.json"
DOCS = [ROOT / "README.md", ROOT / "docs/tutorial.md", ROOT / "docs/demo-script.md", ROOT / "docs/portal.md"]
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
UA = {"User-Agent": "Mozilla/5.0 RoadmapBond-LinkAudit/1.0"}


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
            response = requests.get(direct, headers=UA, timeout=20, allow_redirects=True)
        except requests.RequestException as error:
            print("Direct StudioNet Explorer links: FAIL (" + name + ": " + str(error)[:180] + ")")
            return False
        if response.status_code != 200 or address.lower() not in response.url.lower():
            print("Direct StudioNet Explorer links: FAIL (" + name + " did not resolve to its address page)")
            return False
        print(name + ": PASS " + direct)
    return True


def main():
    proof = json.loads(PROOF_PATH.read_text(encoding="utf-8"))
    ok = audit_local_links()
    explorer_ok = audit_contract_urls(proof)
    if proof.get("chainId") != 61999:
        print("Explorer network: FAIL (expected StudioNet chain 61999)")
        ok = False
    elif explorer_ok:
        print("Explorer network: PASS (StudioNet chain 61999)")
    if not ok or not explorer_ok or proof.get("releaseStatus") != "LIVE_CASES_COMPLETE":
        print("Link audit: NOT COMPLETE; do not hand the Portal packet to a reviewer.")
        return 2
    print("Link audit: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
