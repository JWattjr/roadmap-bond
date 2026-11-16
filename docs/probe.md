# StudioNet evidence access probe

The probe contract fetched these sources from validator execution before the final BondBoard and PromiseJudge deployment.

| Source | HTTP | Bytes | SHA-256 | Result |
|---|---:|---:|---|---|
| wayback_cdx | 200 | 36 | `84154bc9acd6c73a79f95abfc8916e70a684db5c25145cd704a46c16332a47d1` | reachable |
| wayback_id_snapshot (20210105202614) | 200 | 19861 | `7bd80bd12e967a148e1e58e4f56be996ae4600dd07cc23eaaba4bafe483416ec` | reachable |
| github_raw | 200 | 213 | `d2aef47172ca1b9cf98e00258d716de82683649d42510d88fd27ed8ffff44f78` | reachable |
| npm_exact_version | 200 | 4826 | `d02f87f5891f65152f4c4a7314ab03459de08009702edf96ed51a280ea64a8dc` | reachable |
| wikipedia_oldid | 200 | 385888 | `dad26fe1321735204f90bbd07939d46644ceef04dca8d7db9a2a29a7df8c35f5` | reachable |

Only sources with HTTP 200 are included in the release allowlist. Evidence is still keyword-extracted and capped in contract code.
