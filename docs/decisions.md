# Build decisions

These decisions follow the attached, pre-approved build prompt. Historical replays are demonstrations, not current-deadline promises. A mock or direct-mode result is never described as a live StudioNet outcome.

## Product

- StudioNet, chain 61999, RPC `https://studio.genlayer.com/api`, Explorer `https://explorer-studio.genlayer.com`.
- Keep the final release to two distinct contracts: `BondBoard` holds escrow and applies deterministic settlement; `PromiseJudge` compiles criteria and judges one criterion at a time without holding funds.
- Use exact Wayback CDX and snapshot checks, digest-bound evidence capped around 30 KB, no more than three challenge URLs and two defence URLs, and native finalized transfers.
- Generate five team keys, two challenger keys, and one outsider key into ignored `.env`. The approved gross transfers and escrow movements must remain at or below 2,000 wei. No keys or signer prompts go to the owner.
- The local case manifest begins empty. It will only receive real case outcomes after their transactions finalize and pass read-only proof checks.
- Portal fields are prepared in `docs/portal.md`; the form remains unsubmitted.

## Visual direction contract

The product mechanism: an archived sentence becomes a frozen criterion trace, then a challenge and validator evidence determine a finalized bond route. The audience is a reviewer following dated artifacts and state transitions. Its cultural home is the network packet capture and distributed transaction trace. The first surface must show how evidence changes settlement.

The category-default marketing hero and uniform card dashboard are the rut. The Impeccable direction roll ran in degraded mode because its one external roll endpoint was unreachable; its seed assigned grounded candidate 6 (`3b794171`), with no catalog challengers or quality-bar cards. The brief delegates this choice, so the build proceeds on the assigned direction without an approval handoff.

Seven grounded candidates, ordered by resonance:

1. A release train board, where delivery gates and deadlines appear in a single view.
2. A standards change log, where one proposal moves through review states.
3. A library accession register, where the source and its immutable date are primary.
4. An accounting journal, where escrow and every balance movement reconcile.
5. A court evidence bundle, where each claim points to a source and an outcome.
6. A network packet trace, where each callback and state transition forms an auditable route.
7. A maintenance window runbook, where operators see safe next actions and fallback paths.

Candidate 6 is the committed direction. The ledger is a trace index; case pages read as a routed event stream. Cool mineral blue surfaces, paper-white evidence lanes, deep ink text, and copper-orange pending states distinguish live stages without glow effects. Payout paths use explicit recipient and wei rows. Icons and arrows mark real transitions. This applies to the home ledger, promise pages, transaction feed, and empty or stale states.

## Network access probe

The AccessProbe could not be submitted because the configured StudioNet RPC could not resolve `studio.genlayer.com` from this environment (`socket.gaierror: [Errno 11001] getaddrinfo failed`). A read-only chain ID request exhausted its retry loop without a transaction hash. Therefore Wayback `id_`, CDX, pinned GitHub raw, npm, and Wikipedia access are not verified for GenLayer validators. No probe transaction, funding transfer, or final deployment was recorded.

## Publication access

- The GitHub connector identifies `JWattjr` and can read the existing fixture repository, but its content-write call returned HTTP 403 (`Resource not accessible by integration`). `gh auth status` reports the saved token is invalid. The available GitHub browser session is signed out, so neither the public `JWattjr/roadmap-bond` repository nor the pinned injection-fixture commit could be created from this environment.
- The Vercel connector lists the `wattxs-projects` team but project creation for `roadmap-bond` returned HTTP 403 (`You don't have permission to create the project`). The required scoped CLI fallback failed before authentication because it could not fetch npm dist-tags and the Vercel API (`fetch failed`). No Vercel project or deployment was created.
- These publication limitations do not change implementation status. The source remains local, and the Portal packet stays a draft until publication, StudioNet cases, address links, and proof verification are complete.

## Release constraints

- Keep transaction hashes in proof before polling and resume by stable action labels.
- Save the exact source hash for the final deployed contracts; only the final addresses belong in Portal contract evidence.
- `docs/portal.md` must list a separate direct Explorer address link with evidence type `GenLayer Explorer Contract` for each final contract. Do not submit the Portal form.
- No repository publication, funding, deployment, or Portal submission is claimed unless a verifiable receipt is recorded.

## Ship continuation — 2026-11-16

- Registry-backed `npm install` completed, then a clean `npm ci` completed successfully. Both audited 253 packages with zero vulnerabilities, and the committed `package-lock.json` did not change.
- The public application repository is [JWattjr/roadmap-bond](https://github.com/JWattjr/roadmap-bond). Initial source commit `be026a7a19a4ecddb8fc705072d61dfb0717c1da` was pushed to `main`; follow-up release evidence updates will be committed before final deployment.
- The fixture is pinned at commit `86e7aac3b44bf39fc1ede782d4f585c84e6f743c`, path `roadmap-bond/evidence/ai-injection.txt`. The raw URL returned HTTP 200 and SHA-256 `d2aef47172ca1b9cf98e00258d716de82683649d42510d88fd27ed8ffff44f78`.
- The StudioNet RPC responded with chain ID `0xf22f` (61999). CLI network is StudioNet; `moment-grid-studionet` is active and unlocked. The first AccessProbe deployment and source read finalized successfully, but its CDX parser treated the first `urlkey` column as a timestamp. Direct CDX verification found capture `20210105202614`, and the matching `id_` URL returned HTTP 200. The probe now requests `fl=timestamp`; only the diagnostic AccessProbe will be redeployed. No final contract or test-account funding transaction has yet been submitted.
- The revised `contracts/access_probe.py` passes `python -m genvm_linter.cli check contracts/access_probe.py --json` (3 lint checks and SDK validation). The first probe transaction hashes remain in `deploy/proof.json`; the retired probe had no payable functions and holds no funds.
- Vercel created project `wattxs-projects/roadmap-bond`; the first remote production build reached READY and aliased `https://roadmap-bond.vercel.app`. Route checks are pending, and a final deployment will follow the release evidence commit.
- The earlier sandboxed CLI checks failed on blocked DNS/API access, but authorized CLI calls with network access succeeded. The invalid cached `gh` status output was stale; `gh repo create` and subsequent pushes completed successfully.

## Verified ship continuation — 2026-11-16

The initial blocked-access notes above describe the first shell attempt and are superseded by this continuation's successful CLI access.

- StudioNet RPC access is live at chain 61999. The active signer is the pre-approved `moment-grid-studionet` account. The AccessProbe v2 finalized all five configured validator sources; the earlier probe with the CDX column parsing bug is retired and held no funds.
- The public application repository is `https://github.com/JWattjr/roadmap-bond`, and the injection fixture is pinned at commit `86e7aac3b44bf39fc1ede782d4f585c84e6f743c`. The fixture's raw bytes are 213 bytes with SHA-256 `d2aef47172ca1b9cf98e00258d716de82683649d42510d88fd27ed8ffff44f78`.
- The production Vercel project is `roadmap-bond`; its default URL is `https://roadmap-bond.vercel.app`. The first remote build reached READY. The final remote build and required route checks will follow completed live cases.
- Exact CDX rows, archived `id_` fetches, quotes, and permitted challenge evidence were checked for all seven cases. The source and evidence URLs, replay cutoffs, capture timestamps, and fixture digest are recorded in `docs/case-evidence-audit.md`.
- The positive Node.js 20 evidence was strengthened to the archived v20.9.0 LTS transition page: it is timestamped October 24, 2023, and the exact successful CDX capture is November 7, 2023, after the October 31 replay deadline.
- The seven separate records use distinct promise IDs. `deploy/cases.json` now expects: `REJECTED_REFUNDED`, `KEPT`, two `BROKEN` records (including the alpha-only rename case), `UNPROVEN` for the injection fixture, `RELEASED`, and `UNPROVEN` for the React Context codemod evidence.
- The archived Next.js sentence uses “improving”; the deterministic vague-spec guard now also matches “improving” and “improvement”, so the required rejection case does not depend on LLM classification. This edits only the pre-deployment contract source; the final contracts are still undeployed.
- The release runner stages all promises and challenges before waiting for their full configured 1,800-second windows, then settles in a resumable order. Every transaction hash continues to be saved before receipt polling. The window values are unchanged and remain at least 30 minutes.
- Funding plans 890 wei of gross movements, below the approved 2,000 wei cap. The 230-wei seed transfers from `moment-grid-studionet` finalized successfully: 200 wei to the poster signer, 20 wei to Challenger 1, and 10 wei to Challenger 2. Each hash is in `deploy/funding.json` and `deploy/proof.json`; final BondBoard/PromiseJudge deployment remains pending.
- Portal submission remains explicitly out of scope. `docs/portal.md` will contain only separate final contract address entries as **GenLayer Explorer Contract**, plus the website and repository, after addresses have been verified on StudioNet.
