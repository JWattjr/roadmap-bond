# Roadmap Bond

Roadmap promises with a price tag: validators decide if it shipped or just got renamed.

Roadmap Bond turns one sentence from a team's archived roadmap into a bonded commitment. The promise is quoted from an exact Wayback snapshot; validators compile observable criteria; an open challenger can stake against it after the deadline; deterministic contract code routes the bond only after finalized judgments.

**Current release state:** the corrected v3 final pair is deployed on StudioNet: BondBoard `0xBf3C8BA4e2f21ac9a8cF2D91F527299AE40Fd068` and PromiseJudge `0x6b2703a021D92fce49D6F63387b795eA881346A2`. All seven historical cases are posted; the rejected-specification case and refund are final, and the other six are in their full configured windows before settlement. The retired v2 pair has zero escrow and zero native balance. No final outcome is claimed for the staged cases until their judgments, payouts, and callbacks finalize. Consult [`deploy/proof.json`](deploy/proof.json) for the live record. Mocked direct tests are not live proof.

The first shell attempt had network and authentication failures, but the authorized CLI continuation recovered access. See [`docs/decisions.md`](docs/decisions.md) and [`docs/case-evidence-audit.md`](docs/case-evidence-audit.md) for the verified sources and release decisions. No final contract outcome is claimed until its transaction and callbacks finalize on StudioNet. The Portal form is never submitted automatically.

## Architecture

```mermaid
flowchart LR
  Team[Team posts archived quote + bond] --> Board[BondBoard: URL checks, escrow, windows]
  Board --> Archive[Wayback CDX + id_ snapshot]
  Board -->|finalized callback| Judge[PromiseJudge: compile quote into frozen criteria]
  Judge -->|criteria + hash| Board
  Challenger[Open challenger + 25% stake] --> Board
  Poster[Poster defence: up to two immutable URLs] --> Board
  Board -->|one criterion per transaction| Evidence[Bounded fetch, text extract, SHA-256]
  Evidence --> Validators[GenLayer validators judge the extract]
  Validators -->|same digest, verdict, quote| Judge
  Judge -->|finalized callback| Board
  Board --> Settle[Deterministic settlement after finality]
  Settle -->|KEPT: bond + stake| Team
  Settle -->|BROKEN: bond + stake| Challenger
  Settle -->|UNPROVEN: both refunds| Team
  Settle -->|UNPROVEN: both refunds| Challenger
  App[Next.js ledger + case pages] --> Board
  App --> Manifest[deploy/proof.json]
```

`BondBoard` owns escrow, deadlines, state transitions, refunds, release, and payout recipients. `PromiseJudge` holds no funds; it compiles the quote and judges a single criterion against a digest-bound evidence extract. The model returns a verdict and short evidence quote. It cannot choose amounts, winners, or transaction order.

## Settlement paths

| Final state | Contract result |
|---|---|
| Every criterion is `MET` | Poster receives the bond and the challenger's stake. |
| Any criterion is `NOT_MET` | Challenger receives the bond and their stake. |
| No failure, at least one `INSUFFICIENT_EVIDENCE` | Both parties receive their original amounts. |
| No challenge by the end of the challenge window | Poster receives the bond. |
| Compilation or judging exceeds its grace window | Contract provides a refund path; unresolved evidence does not strand funds. |
| Quote cannot become an observable specification | Promise is `REJECTED`; poster can reclaim the bond. |

## Local setup

Requirements: Python with the versions in `requirements.txt`, Node.js compatible with the pinned Next.js package, and the GenLayer CLI for live StudioNet operations.

```powershell
python -m pip install -r requirements.txt
npm ci
python scripts/generate_keys.py
npm run dev
```

The generated demo signers are kept only in `.env`, which is ignored by Git. The key-generation command refuses to overwrite an existing file. Do not print, commit, or send those keys.

Read-only visitors do not need a wallet. Wallet writes use an EIP-1193 provider, switch to StudioNet (chain 61999), and ask the provider to sign. Contract calls and scripted release operations are covered in `docs/tutorial.md`.

## Validate and release

```powershell
npm run test:contract
npm run lint:contracts
python scripts/build_fixture.py
python scripts/probe.py
python scripts/fund_accounts.py
npm run release
npm run audit:links
npm run verify:proof
```

The required validator access probe runs before the two final contracts. Verify every historical snapshot and evidence URL through CDX, then mark `deploy/cases.json` ready with the pinned fixture commit and exact quotes. A deployment is not complete until probe results, final source hashes, every transaction and callback, each live case, the direct Explorer address pages, and the read-only proof verifier are recorded. The Portal form remains a human action; `docs/portal.md` is a prepared packet only.

## App behavior

- `/` is the promise ledger. It shows live StudioNet state when available and labels the recorded proof fallback separately.
- `/promise/<id>` shows the archived quote, frozen criteria and hash, windows, challenge and defence evidence, per-criterion quote/digest/reason, payout movements, and transaction states.
- `/api/proof` returns the release manifest.
- `/api/live` reads the latest finalized Board records, caches good reads for 60 seconds, and returns the last good or recorded proof state when RPC reads fail.
- Explorer links use `/address/<address>` and `/tx/<hash>` on the StudioNet Explorer.

## Honest limitations

- Wayback capture availability is external. Both the exact CDX row and archived page need to load when a promise is posted.
- Only Wayback `id_`, SHA-pinned `raw.githubusercontent.com`, exact npm versions, and Wikipedia `oldid` URLs are eligible evidence. The pre-deployment probe is required; unsupported sources must be removed from the final evidence allowlist.
- Text excerpts are limited to about 30 KB across sources. Oversized, unavailable, or irrelevant evidence becomes `INSUFFICIENT_EVIDENCE`; it does not establish fault.
- The model and validators are not a legal court. The contract stores their result, and GenLayer's native appeal window still applies before finality.
- `post_replay` is owner-only and exists for clearly labeled historical demonstrations. Production `post` still enforces a deadline at least 60 minutes ahead.
- Anyone may post a production promise. The archived quote must be the poster's public statement; the current contract cannot prove that the poster legally represents a project.
- No live case outcomes are included until finalized on StudioNet and accepted by `scripts/verify_proof.py`.

## Release history

- **Local implementation:** `BondBoard` and `PromiseJudge` are the only final contract sources. `AccessProbe` is a pre-release probe source, not a final contract and not Portal evidence.
- **Validator probes:** AccessProbe v1 (`0x05D0e33CCA945Bce2e05448C7A25FD3fFf3640c2`) was retired after a CDX response-column parsing error. AccessProbe v2 (`0xa9219dd18974B0d6f4Dd4FE8a212eBeCb5e4C6B6`) finalized all five validator-source checks. Both probe addresses were verified at zero wei and neither is Portal evidence.
- **Retired release attempt:** the first BondBoard and PromiseJudge pair (`0xF35a25a0B0DD3946331d18251D184c26777ADDdE` and `0xFFf71769AEfCE77E15ff82ac8b796EcC7780f1f1`) had a compile callback cancel with `NO_MAJORITY`. After its 30-minute grace, the 40-wei bond refund finalized in `0xd7777a33021b1f28b51f847578098de6a5a850c2cddf67956f020758b9019349`; both product contract balances are verified at zero. Neither address belongs in Portal evidence.
- **Retired v2 pair:** BondBoard `0x4115a88A6B3350dD3AbF60b4893221Fd8514566a` and PromiseJudge `0xeA868d6B06871e7953Bb7D37757Aa9D11cad8255` are retired. Their seven case records are archived in proof with every payout finalized; Board escrow and both native contract balances are zero. The two Node.js 20 positive-case attempts finalized `UNPROVEN` with `LLM_ERROR` and were fully refunded. Neither v2 address belongs in Portal evidence.
- **Corrected demo inputs:** on the active v2 pair, the long rename-only quote and the initial React Compiler wording were rejected and refunded. A first injection retry at `promise-7` also refunded after its stale snapshot URL failed exact quote verification. The manifest now uses the matching React 19 Beta capture and replays the ref-prop codemod promise under `promise-8`; the intended seven outcomes remain separate records.
- **v2 retirement and corrected final pair:** Node.js 20 attempts `promise-2` and `promise-11` both finalized with `LLM_ERROR`; both bonds and stakes were refunded. The evidence pages are available, and contract inspection found that judge validation repeated the nondeterministic leader call while strict output checks converted response-format differences to `LLM_ERROR`. The corrected `PromiseJudge` removes that duplicate model call, validates the immutable evidence digest and quote directly, accepts harmless JSON wrappers/extra keys, bounds the stored reason, and retries one invalid response. Open v2 promises are being finalized or grace-refunded and the pair will be retired at zero balance before the corrected pair is deployed.
- **Publication:** the public GitHub repository and production Vercel project are active; the remote production build and required route checks will be repeated after the finalized proof manifest is complete.

## Documentation

- [`docs/tutorial.md`](docs/tutorial.md) — contract and frontend walkthrough.
- [`docs/demo-script.md`](docs/demo-script.md) — two-minute reviewer tour.
- [`docs/probe.md`](docs/probe.md) — finalized validator access probe results.
- [`docs/case-evidence-audit.md`](docs/case-evidence-audit.md) — exact archive captures, quotes, challenge evidence, and CDX checks for all seven cases.
- [`docs/portal.md`](docs/portal.md) — unsubmitted contribution packet.
- [`docs/decisions.md`](docs/decisions.md) — implementation and release decisions.
