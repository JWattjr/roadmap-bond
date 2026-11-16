# GenLayer Portal submission packet

**Status:** draft only. No form was submitted. Do not hand this packet to the Portal reviewer until the final contracts, required live cases, application URL, repository URL, direct Explorer links, and `npm run verify:proof` are complete.

## Contribution type

Projects

## One-line pitch

Roadmap promises with a price tag: validators decide if it shipped or just got renamed.

## Description

Roadmap Bond turns a team's archived roadmap sentence into an escrowed promise. Validators compile observable criteria from the exact quote. After its deadline, any eligible challenger can stake 25% of the bond and submit immutable evidence; the poster can defend with up to two more sources. GenLayer validators judge one criterion at a time against bounded, digest-matched extracts. Deterministic contract code returns the bond and stake to the poster when every criterion is met, pays both to the challenger when any criterion is not met, and refunds both parties when evidence is inconclusive. A vague promise is rejected with a bond refund. The app exposes the archive, frozen criteria, evidence, verdicts, transaction finality, balance movements, and direct StudioNet Explorer records.

## Reviewer steps

1. Open the production site and confirm the live-read or recorded-proof label.
2. Open the finalized kept promise; compare its quote to the exact Wayback snapshot, then inspect the frozen criteria hash and each digest-bound verdict.
3. Open the broken/rename-only case and compare the evidence with `not_counted`, the `NOT_MET` verdict, and the challenger payout.
4. Open the injection/unproven case; inspect the pinned fixture text and verify that untrusted instructions do not force `MET`, then check the refund trail.
5. Open the rejected-spec and unchallenged cases to inspect the finalized refund and bond release.
6. Open `BondBoard` and `PromiseJudge` through their separate direct StudioNet Explorer contract-address links below. Compare the deployment transactions and source hashes with `deploy/proof.json`.
7. Run `npm run verify:proof` and confirm that all final addresses, source hashes, chain reads, and transaction records pass.

## Expected outcome

After a complete live release, five historical replay promises cover the required seven case types: one vague quote is rejected and refunded; one promise is kept and pays the poster; one promise is broken because a name-only or experimental release does not meet the frozen criterion; one instruction-bearing pinned fixture is ignored and produces an unproven refund when the available evidence cannot decide; and one promise receives no challenge and is released after its full window. Each case must be backed by finalized StudioNet transactions. Overlapping a required case label does not replace any missing finalized state.

## Evidence entries

No contract has been deployed, so there are no valid Explorer contract address links to enter yet. Do not invent an address or substitute a transaction link. Once the final contracts are deployed, add each address as a separate row, verify that the direct URL opens the correct StudioNet contract record, and select **GenLayer Explorer Contract** in the Portal.

| Evidence type | Label | URL |
|---|---|---|
| GenLayer Explorer Contract | BondBoard — StudioNet | Pending final deployment and link verification |
| GenLayer Explorer Contract | PromiseJudge — StudioNet | Pending final deployment and link verification |
| Website | Roadmap Bond production app | Pending production deployment |
| GitHub repository | Roadmap Bond source | Pending public repository creation |

## Current blockers

- Validator access to Wayback, CDX, raw GitHub, npm, and Wikipedia has not passed the required StudioNet probe. The StudioNet RPC could not resolve `studio.genlayer.com` (`[Errno 11001] getaddrinfo failed`).
- Neither final contract has a deployed address; no historical case has finalized on-chain.
- The GitHub write connector returned HTTP 403, and the saved `gh` token is invalid. The available browser session is signed out, so the public repository and pinned injection-fixture commit have not been published.
- Vercel project creation returned HTTP 403 for the available team. The scoped CLI fallback could not fetch npm/API metadata, so no production project or deployment exists.
- The contract Explorer links cannot be checked against a live StudioNet record until deployment.

The Portal submission must remain with the owner. This packet is not a submission and the current draft is not submission-ready. When final contracts exist, add each direct `/address/<contract>` Explorer URL as its own **GenLayer Explorer Contract** evidence row and open it on StudioNet before handing the packet over.
