"""Generate the demo-only signers into the ignored .env without printing keys."""

import json
from pathlib import Path

from eth_account import Account


ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
MANIFEST = ROOT / "deploy/funding.json"


def main():
    if ENV.exists():
        raise SystemExit("Refusing to overwrite existing .env")
    names = [f"TEAM_{i}" for i in range(1, 6)] + ["CHALLENGER_1", "CHALLENGER_2", "OUTSIDER"]
    accounts = {name: Account.create() for name in names}
    ENV.write_text("\n".join(f"{name}_PRIVATE_KEY=0x{account.key.hex().removeprefix('0x')}" for name, account in accounts.items()) + "\n", encoding="utf-8")
    try:
        ENV.chmod(0o600)
    except OSError:
        pass
    proof = json.loads(MANIFEST.read_text(encoding="utf-8"))
    proof["wallets"] = {name.lower(): account.address for name, account in accounts.items()}
    proof["transfers"] = {}
    proof["status"] = "KEYS_GENERATED"
    MANIFEST.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print("Generated 5 team, 2 challenger and 1 outsider keys in ignored .env.")
    for name, account in accounts.items():
        print(f"{name.lower()}: {account.address}")


if __name__ == "__main__":
    main()
