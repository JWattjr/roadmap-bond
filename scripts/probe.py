"""Deploy the source-access probe before the production contracts."""

import hashlib
import json
from pathlib import Path

from chain import ROOT, load_proof, read, save_proof, tx


def main():
    proof = load_proof()
    source_path = ROOT / "contracts/access_probe.py"
    source = source_path.read_text(encoding="utf-8")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    probes = proof.setdefault("probeContracts", {})
    current = probes.get("AccessProbe")
    if current and current["sha256"] != digest:
        proof.setdefault("retiredProbeContracts", []).append({
            **current,
            "retiredReason": "The first CDX response included urlkey before timestamp; the probe parser now requests timestamp-only output.",
        })
        if proof.get("probeResults"):
            proof.setdefault("probeResultsHistory", []).append(proof["probeResults"])
        del probes["AccessProbe"]
        save_proof(proof)
    if "AccessProbe" not in probes:
        deploy_label = "probe-deploy" if "probe-deploy" not in proof["transactions"] else "probe-deploy-v2"
        receipt = tx(proof, deploy_label, code=source)
        address = receipt.get("recipient", receipt.get("to_address"))
        if not address:
            raise RuntimeError("Probe deploy finalized without an address")
        probes["AccessProbe"] = {"address": address, "source": "access_probe.py", "sha256": digest}
        save_proof(proof)
    elif probes["AccessProbe"]["sha256"] != digest:
        raise RuntimeError("Probe source differs from its deployed source hash")

    target = "https://www.isc.org/blogs/2020-accomplishments/"
    raw = "https://raw.githubusercontent.com/JWattjr/bounty-bench-fixtures/86e7aac3b44bf39fc1ede782d4f585c84e6f743c/roadmap-bond/evidence/ai-injection.txt"
    npm = "https://registry.npmjs.org/typescript/5.0.2"
    wikipedia = "https://en.wikipedia.org/w/index.php?title=TypeScript&oldid=1070886749"
    label = "probe-sources" if "probe-sources" not in proof["transactions"] else "probe-sources-v2"
    if label not in proof["transactions"]:
        tx(proof, label, address=probes["AccessProbe"]["address"], method="probe", args=[target, raw, npm, wikipedia])
    result = read(probes["AccessProbe"]["address"], "get_result")
    probe_result = json.loads(result) if isinstance(result, str) else result
    proof["probeResults"] = probe_result
    save_proof(proof)
    (ROOT / "docs/probe.md").write_text(render(probe_result), encoding="utf-8")
    print(json.dumps(probe_result, indent=2))


def render(result):
    lines = [
        "# StudioNet evidence access probe",
        "",
        "The probe contract fetched these sources from validator execution before the final BondBoard and PromiseJudge deployment.",
        "",
        "| Source | HTTP | Bytes | SHA-256 | Result |",
        "|---|---:|---:|---|---|",
    ]
    for row in result.get("results", []):
        name = row.get("source", "")
        if name == "wayback_id_snapshot" and row.get("capture_ts"):
            name += " (" + row["capture_ts"] + ")"
        status = "reachable" if row.get("reachable") else "unavailable"
        lines.append(f"| {name} | {row.get('status', '')} | {row.get('bytes', '')} | `{row.get('sha256', '')}` | {status} |")
    lines.extend(["", "Only sources with HTTP 200 are included in the release allowlist. Evidence is still keyword-extracted and capped in contract code.", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
