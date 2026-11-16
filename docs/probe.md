# StudioNet evidence access probe

## Status: not deployed, not verified

The required probe contract has not been submitted. A read-only StudioNet chain ID request exhausted the RPC retry loop because the environment could not resolve `studio.genlayer.com` (`socket.gaierror: [Errno 11001] getaddrinfo failed`). No write was submitted and no transaction hash exists; `deploy/proof.json` contains no probe transaction. No source is reported as reachable from GenLayer validators.

| Required source | Validator result | Allowlist decision |
|---|---|---|
| Wayback `id_` snapshot | Not probed | Pending validator probe |
| Wayback CDX JSON | Not probed | Pending validator probe |
| SHA-pinned `raw.githubusercontent.com` file | Not probed | Pending validator probe |
| Exact npm registry version | Not probed | Pending validator probe |
| Wikipedia `oldid` page | Not probed | Pending validator probe |

The local URL-shape checks are implementation behavior, not proof of network fetch access. Before any contract deployment, run `python scripts/probe.py`, record the finalized result in `deploy/proof.json`, remove failed source types from the final source's allowlist, and rerun contract tests and lint. The owner should be given only verified direct Explorer links after a probe or final contract transaction appears in the manifest.
