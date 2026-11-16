# Roadmap Bond implementation tutorial

This walkthrough follows the local implementation in `contracts/bond_board.py`, `contracts/promise_judge.py`, `lib/server-chain.ts`, and the release scripts. The design keeps evidence judgment separate from escrow: `PromiseJudge` may return a verdict, but `BondBoard` alone owns the money and state transitions.

## 1. A public sentence becomes an escrowed record

The production `BondBoard.post` method is payable. It receives a Wayback `id_` snapshot URL, one quote, and a Unix deadline; the sent value is the bond. `_start_post` records the sender, deadline, bond, configured challenge, defence, and grace windows, and rejects an ordinary deadline less than an hour in the future. It also checks that the quote length is between 20 and 300 characters and that `PromiseJudge` has been configured.

Snapshot validation is deliberately outside the language model. `verify_snapshot` parses the exact fourteen-digit Wayback timestamp, restricts the captured target to public HTTPS, asks CDX for a successful row at that exact timestamp, loads the `id_` page, normalizes whitespace, and checks that the quote occurs verbatim. The contract uses `strict_eq` so validators independently run those reads. If the URL, capture, fetch, or quote check fails, the record moves to `REFUNDABLE_ERROR` and a finalized self-call schedules the refund. A payable mistake therefore remains visible and recoverable rather than being silently retained.

`post_replay` is separate. Only the Board owner can use it, it requires a past deadline, and the UI labels the resulting record as a historical replay. This keeps demonstration history out of the normal production path.

## 2. Validators compile a narrow specification

After the snapshot check, the Board emits `PromiseJudge.compile` through `emit(on="finalized")`. Vague language such as “improve”, “better”, or “across the board” is rejected deterministically without an LLM call. For other quotes, the model classifies whether the sentence describes a concrete public deliverable and supplies short reasons. The Board freezes the exact archived sentence as one criterion, hashes it, and applies a canonical `not_counted` rule so the criterion cannot expand beyond the source quote.

The `run_nondet_unsafe` validator checks the proposed status, exact quote criterion, canonical rule, hash, and reason shape without rerunning the LLM. This keeps validation deterministic while still requiring validators to agree on the same stored result. `BondBoard.complete_compile` stores the frozen criterion, hash, and reasons. An accepted result becomes `OPEN`; a rejected result becomes `REJECTED`, and the poster can call `refund_rejected`. The criteria hash lets reviewers confirm that the words shown in the UI are the criterion actually stored for judgment.

## 3. A challenge stakes against the promise

Once the deadline passes, any address except the poster can challenge an open promise. `BondBoard.challenge` requires exactly one quarter of the bond and one to three evidence URLs. `valid_evidence_url` limits evidence to an archived Wayback `id_` snapshot dated on or after the deadline, a SHA-pinned raw GitHub path, one exact npm version, or a Wikipedia revision pinned by `oldid`. A mutable page is not accepted. The poster may add up to two more eligible sources before the defence deadline.

Invalid payable challenges are recorded under `refunds` and emitted for a finalized `pay_refund` callback. Valid challenges record the challenger, stake, source URLs, and the end of the defence window. The public promise view stores those details, so the application can render them without an indexer.

## 4. Each criterion uses a bounded evidence extract

After the defence window, anyone can call `judge_next`. The Board picks only the next frozen criterion, combines the challenger and defence URLs, marks the promise `JUDGING`, and emits a finalized call to `PromiseJudge.judge`.

The Judge re-fetches the allowed sources with a browser user agent, strips HTML and script/style sections, converts common entities, and builds short keyword windows around the criterion's key nouns. It caps the combined text at 30,000 bytes and hashes the exact text sent to the model. A failed fetch, oversized source, or missing relevant passage becomes `INSUFFICIENT_EVIDENCE` without asking the model to decide.

For an available extract, the prompt says the evidence is untrusted data and embedded instructions must be ignored. It includes the frozen `not_counted` rule. The model returns only `MET`, `NOT_MET`, or `INSUFFICIENT_EVIDENCE`, a short reason, and a verbatim quote. Every validator re-fetches and re-extracts, compares the digest and verdict, and checks that the quote occurs in its own extract. The Judge calls `complete_judgment` through a finalized callback; the Board stores the criterion, quote, digest, class, reason, verdict, and timestamp.

## 5. Contract code determines every transfer

When all criteria have a result, the Board schedules `settle` as a self-only finalized callback. `_finalize_settlement` is deterministic: any `NOT_MET` means `BROKEN`; otherwise any inconclusive result means `UNPROVEN`; only all-`MET` results mean `KEPT`. The amounts and recipients come from stored fields, never model output.

For `KEPT`, the poster receives the bond and stake. For `BROKEN`, the challenger receives both. For `UNPROVEN`, the Board refunds the bond and stake to their original parties. `_payout` stores a finalized payout audit row on the promise and emits the native transfer. The no-challenge `release` path returns the poster's bond after the full challenge window. `settle_expired` inserts `INSUFFICIENT_EVIDENCE` results for unjudged criteria after the configured judging grace period, so an unresolved child call does not lock the escrow forever. Compilation expiry has its own refund action.

## 6. The app reads from the final contract state

The Next.js server-side `snapshot` reads `get_promises` using GenLayer JS's `LATEST_FINAL` transaction variant. `/api/live` caches a good snapshot for 60 seconds; if StudioNet fails, it returns the last good read, or the recorded manifest marked as recorded when a server instance has no good read yet. `/api/proof` serves the separate release manifest. The ledger and `/promise/<id>` pages label these sources separately.

Case pages display the exact archived source, frozen criteria and hash, challenge and defence URLs, the `not_counted` rule, individual verdict quotes and digests, balances, payout audit entries, transaction links, and pending/accepted/finalized states. Wallet reads are unnecessary. Write actions use the EIP-1193 bridge and the StudioNet chain; contract checks still enforce who may perform each action.

## 7. Scripts and verification

`scripts/generate_keys.py` writes eight demo signers to ignored `.env` without printing private keys. `scripts/fund_accounts.py` saves each source transfer hash before polling and enforces the recorded gross movement plan. `scripts/chain.py` assigns stable labels to writes, persists each transaction hash before waiting, and follows finalized callback children. `scripts/lint_contracts.py` lints the two final contracts and the access probe. Direct tests mock web and LLM responses, including double-encoded JSON; they verify contract behavior but do not count as live cases.

`deploy/proof.json` is the public receipt manifest. `scripts/verify_proof.py` checks StudioNet chain ID, final contract source hashes, final Explorer contract records and direct address URLs, and every recorded transaction. The verifier is read-only. Until the probe, contracts, all required cases, links, and verifier pass live, the release status remains incomplete.
