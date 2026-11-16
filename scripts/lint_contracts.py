"""Run the pinned GenVM linter on the final contracts and access probe."""

import json
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ["contracts/bond_board.py", "contracts/promise_judge.py", "contracts/access_probe.py"]


def command_for(source):
    executable = shutil.which("genvm-lint") or shutil.which("genvm-lint.exe")
    if not executable:
        scripts = Path(sysconfig.get_path("scripts"))
        names = ["genvm-lint.exe", "genvm-lint"] if os.name == "nt" else ["genvm-lint"]
        executable = next((str(scripts / name) for name in names if (scripts / name).exists()), None)
    if executable:
        return [executable, "check", str(ROOT / source), "--json"]
    return [sys.executable, "-m", "genvm_linter.cli", "check", str(ROOT / source), "--json"]


def main():
    failed = False
    for source in CONTRACTS:
        result = subprocess.run(command_for(source), cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(source, "could not parse linter output")
            print(result.stdout[-1500:])
            print(result.stderr[-1500:])
            failed = True
            continue
        ok = result.returncode == 0 and report.get("ok") is True
        print(source, "PASS" if ok else "FAIL")
        if not ok:
            print(json.dumps(report.get("lint", {}), indent=2))
            failed = True
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
