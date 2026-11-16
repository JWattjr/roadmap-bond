# GenLayer Portal submission packet

**Status:** prepared draft; no form has been submitted. The owner submits the Portal entry. Before handoff, all seven live cases, `npm run verify:proof`, the complete link audit, and both direct StudioNet Explorer contract links must pass.

## Contribution type

Projects

## One-line pitch

Roadmap promises with a price tag: validators decide if it shipped or just got renamed.

## Description

Roadmap Bond turns a team's archived roadmap sentence into an escrowed commitment. Validators compile observable criteria from the exact quote. After its deadline, an open challenger can stake 25% of the bond and submit immutable evidence; the poster may defend with up to two more sources. Validators judge one criterion at a time against bounded, digest-matched extracts. Deterministic contract code returns the bond and stake to the poster when every criterion is met, pays both to the challenger when any criterion is not met, and refunds both sides when evidence is inconclusive. A vague promise is rejected with a bond refund. The app exposes the archive, frozen criteria, evidence, verdicts, transaction finality, balance movements, and direct StudioNet Explorer records.

## Reviewer steps

1. Open the production site and confirm the StudioNet chain label and whether the page is showing live reads or recorded proof.
2. Open `promise-1` and inspect the Next.js quote, `SPEC_REJECTED` reason, and finalized refund.
3. Open `promise-2`; compare its quote with the exact Node.js 20 archive capture, then inspect the frozen criterion, Node v20.9.0 evidence, `MET` verdict, and poster payout.
4. Open `promise-3`; compare the Rust 2024 H2 deadline with the Rust 1.85.0 release evidence, `NOT_MET` verdict, and challenger payout.
5. Open `promise-5`; inspect the Next.js 13.4 `next build --turbo` promise, the Next.js 15.3 alpha label, the frozen `not_counted` rule, and the `BROKEN` settlement.
6. Open `promise-7`; inspect the SHA-pinned injection fixture and verify it did not force `MET`; the correct result is `INSUFFICIENT_EVIDENCE` and both parties are refunded.
7. Open `promise-8` and confirm the unchallenged Node.js 22 bond released only after the full window. Open `promise-9` and confirm the React 19 evidence cannot establish the promised Context-provider codemod, so both parties are refunded.
8. Open the two separate direct StudioNet Explorer contract-address links below. Confirm each opens the matching contract record. Compare their source hashes and all transaction records with `deploy/proof.json`.
9. Run `npm run verify:proof` and confirm all contract, case, source, and transaction checks pass.

## Expected outcome

Seven finalized StudioNet historical replays: Next.js's vague improvement quote is rejected and refunded; Node.js 20 is kept and returns bond plus stake to the poster; the Rust 2024 edition misses its 2024 H2 stabilization deadline; Next.js Turbopack's alpha production build does not satisfy the earlier production-support promise; the instruction-bearing fixture does not force a `MET` verdict; Node.js 22 is released after an unchallenged full window; and the React Context codemod remains unproven by the chosen evidence. Mocked direct tests are not live proof.

## Evidence entries

| Evidence type | Label | URL |
|---|---|---|
| GenLayer Explorer Contract | BondBoard — StudioNet | Pending final contract address |
| GenLayer Explorer Contract | PromiseJudge — StudioNet | Pending final contract address |
| Website | Roadmap Bond production app | https://roadmap-bond.vercel.app |
| GitHub repository | Roadmap Bond source | https://github.com/JWattjr/roadmap-bond |

The two contract entries remain separate and use the Portal's **GenLayer Explorer Contract** evidence type. Do not substitute transaction links for either address page. Do not submit the form automatically.
