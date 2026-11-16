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

## First live consensus failure and recovery — 2026-11-16

- The first deployed pair was `BondBoard` at `0xF35a25a0B0DD3946331d18251D184c26777ADDdE` and `PromiseJudge` at `0xFFf71769AEfCE77E15ff82ac8b796EcC7780f1f1`. The `post-spec_rejected` transaction finalized, but its compile callback `0x8640808f116879699b85cc69e1846dc9f35532ce0f51ffbdc57317cd8d7b9567` canceled with `NO_MAJORITY` / `max_recovery_cycles_exceeded`.
- Diagnosis: the v1 compiler ran an LLM during `leader()` and called `leader()` again in every validator's `validate()` function, then compared generated criteria and prose exactly. That made consensus depend on identical model output. The canceled child left the 40-wei promise bond in the v1 Board; after the built-in 1,800-second grace, `refund_compile_expired` and both payout callbacks finalized. Refund transaction: `0xd7777a33021b1f28b51f847578098de6a5a850c2cddf67956f020758b9019349`; final payout callback: `0x601f118ab020048d47b78f001f08606592c00da19e530506c203c8a4737977e8`.
- Fix for the replacement pair: reject broad improvement goals deterministically before any LLM call; for other quotes, freeze the exact archived sentence as the single criterion with a canonical `not_counted` rule; validate status, hash, rule, and reason shape without rerunning the LLM. The positive `KEPT` case will be replayed live with the full seven-case set after this prompt change.
- This consensus failure made a replacement pair unavoidable. The resumable retirement script verified the v1 promise status is `REFUNDED_INVALID`, both retired product contracts have zero native balance, and both diagnostic probes have zero wei. It records the canceled child as an explicitly documented failed transaction. The replacement pair will be the only final pair listed in the Portal packet; retired addresses remain in README release history only.

## Corrected rename-only replay input — 2026-11-16

- On the final v2 pair, the original long Next.js 13.4 quote finalized through the compiler's safe rejection fallback as `REJECTED`; the callback itself finalized successfully and did not fail consensus. The 40-wei attempt bond was returned through `refund_rejected`; refund transaction `0x88306ca8a9e44a53a956addf9367d7d7ac842537de705b050fbdf34a8e807d17` and its callback tree are recorded in proof.
- I kept the v2 contract pair and chose a shorter exact sentence from the same verified Next.js 13.4 Wayback capture: “Stay tuned for a future Next.js version where you'll be able to run next build --turbo for instant builds.” CDX and the `id_` snapshot both returned HTTP 200, the quote matched exactly, and the after-deadline Next.js 15.3 evidence capture was rechecked through CDX and `id_`.
- The intended rename-only replay uses `promise-5`. Its successful compile and challenge were finalized under a new resumable `v2b` label prefix. This is a case-input retry, not a contract redeployment or a prompt change; the already-finalized positive `KEPT` replay remains the required live check for the v2 compiler change.

## Corrected injection replay input — 2026-11-16

- The first injection-case attempt on `promise-6` was rejected by the compiler because the React Compiler quote described work toward a release rather than a concrete public deliverable. The reason was recorded as `Working to ship and preparing a release do not promise a completed public deliverable.` Its 40-wei bond was refunded; transaction `0x1e854f919a584b7cc60c6c604b8cc8813302aad06c0bab9386be7fa7364ac763` and callbacks are recorded in proof.
- The replacement quote is the concise exact React 19 Beta sentence fragment “we will be publishing a codemod to automatically update your components to use the new ref prop.” The exact CDX row, archived `id_` page, quote match, and pinned injection fixture digest were rechecked. It is a distinct, concrete codemod promise from the Context-provider codemod retained for the separate unproven case.
- The shorter codemod quote was first posted under `promise-7`, but that attempt used the older React Labs `snapshotUrl` from the previous quote. The Board correctly rejected the snapshot mismatch and finalized its automatic 40-wei refund before compilation. The case now resumes as `promise-8`; unchallenged and unproven use `promise-9` and `promise-10`. The runner uses the `v2d` case-label prefix to avoid reusing hashes. No contract source or prompt changed, so the v2 pair and finalized `KEPT` replay remain valid.

- A concurrent zero-value `record_transaction` write returned a Cloudflare 502 without a hash. The marker `v2c-record-injection-f755930d84` was resolved only after the exact call was absent from the Explorer, the TEAM_1 latest and pending nonces matched, and promise-7's payout callback was confirmed final. Proof records this as `NOT_SUBMITTED`; no duplicate write was sent.
