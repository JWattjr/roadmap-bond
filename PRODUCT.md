# Product

<!-- impeccable:product-schema 1 -->

## Platform

Web application on Next.js, TypeScript client, and GenLayer StudioNet intelligent contracts, with Python scripts for release and proof.

## Users

- Open-source maintainers who want their public roadmap statements to carry a verifiable commitment.
- Challengers who can stake against a promise using dated, immutable public evidence.
- Reviewers who need to inspect the original words, frozen criteria, validator evidence, and finalized money movement.

## Product Purpose

Roadmap Bond converts a team's archived roadmap sentence into an escrowed promise. Validators compile observable criteria from the quote, a challenger can stake 25% of the bond with immutable evidence after the deadline, and deterministic contract code settles the bond and stake only after finalized judgments.

Success means a reviewer can follow one case from archived quote to criteria, challenge, defence, criterion judgments, transaction finality, and payout without an indexer or a connected wallet.

## Positioning

“Roadmap promises with a price tag: validators decide if it shipped or just got renamed.” The promise comes from the team's own archived words; the open challenger stakes against the team; the frozen criteria and contract code control settlement. It has no funder, named recipient, leaderboard, partial payout, token, or custom appeal court.

## Operating Context

Visitors inspect a promise ledger and case pages without a wallet. A team posts a quote taken verbatim from an exact Wayback snapshot and locks a bond. Validators accept or reject observable criteria derived from that quote. After the deadline, a challenger can post one to three immutable evidence URLs and a stake equal to one quarter of the bond. The poster can add up to two evidence URLs during the defence window. Anyone can judge one criterion per transaction. Wallet actions include posting, challenging, defending, judging, releasing, and triggering elapsed-window fallbacks.

Historical replays use owner-only `post_replay` and must be labeled clearly in the app and README. They preserve past deadlines for demos; ordinary `post` still requires a deadline at least 60 minutes ahead.

## Capabilities and Constraints

- Snapshot posts require an exact Wayback `id_` URL, exact CDX capture, a normalized verbatim quote of 20–300 characters, and a public HTTPS target.
- Each challenge and defence source must match the narrow immutable URL allowlist. Evidence extracts are capped at 30 KB and digest-bound across validators.
- Evidence is untrusted input. Validators return only a verdict, quote, digest, class, and short reason; contract code owns amounts, status transitions, and recipients.
- `MET` for all criteria returns the bond and pays the challenger's stake to the poster. Any `NOT_MET` pays bond plus stake to the challenger. Any inconclusive criterion without a failure refunds both parties.
- Every configured window is at least 30 minutes. Production deadlines are at least 60 minutes ahead. Compile and judge grace paths return funds rather than locking them indefinitely.
- StudioNet is the demo network (chain 61999). Recorded proof and live reads are labeled separately. Wallet reads remain unnecessary.
- The requested demo is desktop-only; no mobile checks are in scope.

## Brand Commitments

The product name, one-line pitch, StudioNet stack, desktop-only scope, proof requirements, and delegated choice of visual direction are set by the attached build prompt. The first surface must expose the full promise-to-settlement mechanism and distinguish historical replay from a live contract record.

## Evidence on Hand

No Roadmap Bond contract or demo case is deployed when this product record is written. Only a receipt in `deploy/proof.json` that passes `scripts/verify_proof.py` counts as live proof. Mocked tests and prepared cases must never be presented as live outcomes.

## Product Principles

1. The archive fixes what was promised; frozen criteria fix what gets judged.
2. Evidence availability must not punish a party or strand value.
3. The model returns a criterion verdict; deterministic code settles funds.
4. Each verdict must carry its evidence quote and digest.
5. Recorded proof and current StudioNet reads are labeled distinctly.
