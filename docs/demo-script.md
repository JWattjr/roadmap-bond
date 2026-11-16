# Two-minute reviewer tour

This script is for a completed release. The current manifest has no deployed contracts or finalized cases, so do not present it as a live demonstration yet.

**0:00–0:20 — Start at the ledger.** Open the production site and point to the StudioNet chain label and the read-source state. Explain that each row is one archived promise and that historical replays are marked. Open the proof manifest to show that the page distinguishes live reads from recorded proof.

**0:20–0:45 — Open the kept case.** Follow the exact Wayback snapshot link and compare the quoted sentence. Show the frozen criteria and SHA-256 hash. Point out the `not_counted` rule before opening the challenge evidence. Read the criterion quote, evidence digest, evidence class, and short reason.

**0:45–1:10 — Show the broken and rename-only outcome.** Open the promise where the delivered name did not satisfy the observable criterion. Compare its pinned evidence with the criterion, then show `NOT_MET`, the final `BROKEN` status, and the challenger payout. Explain that matching a name or publishing an experimental stub does not satisfy the frozen rule by itself.

**1:10–1:30 — Show the injection and unproven case.** Open the pinned fixture evidence containing the instruction-like text. Show that it is treated as untrusted evidence. Point out the digest-bound extract and the validator verdict. If the extract cannot establish delivery either way, the correct result is `INSUFFICIENT_EVIDENCE`, and both parties are refunded.

**1:30–1:45 — Show the rejected and unchallenged paths.** Open the vague quote, read the compiler reason, and show the finalized bond refund. Then open the unchallenged record and show that release required the full challenge window.

**1:45–2:00 — Close on finality.** Open the direct StudioNet Explorer address for `BondBoard`, then `PromiseJudge`, each as a separate contract record. Open one settlement transaction and its callback children. Finish on `npm run verify:proof` output; it must pass before describing the packet as submission-ready.
