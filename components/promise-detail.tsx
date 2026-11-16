"use client";

import { ArrowLeft, ArrowRight, ExternalLink, FileCheck2, FileClock, Fingerprint, Gavel, Link2, RefreshCw, ShieldCheck, Wallet } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import type { Proof, PromiseRecord, Snapshot, TxState, TxView } from "@/lib/domain";
import { short } from "@/lib/domain";
import { walletAccount, write } from "@/lib/wallet";

const EXPLORER = "https://explorer-studio.genlayer.com";

function statusTone(status: string) {
  if (["OPEN", "KEPT", "RELEASED", "REJECTED_REFUNDED", "MET"].includes(status)) return "tone-good";
  if (["COMPILING", "CHALLENGED", "JUDGING", "READY_TO_JUDGE", "RESULT_PENDING", "ACCEPTED"].includes(status)) return "tone-wait";
  if (["BROKEN", "REJECTED", "REFUNDABLE_ERROR", "REFUNDED_INVALID", "NOT_MET"].includes(status)) return "tone-bad";
  return "tone-neutral";
}

function dateLabel(seconds?: number) {
  return seconds ? new Date(seconds * 1000).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) : "Not recorded";
}

function secondsLeft(seconds?: number) {
  if (!seconds) return "Not scheduled";
  const delta = seconds - Math.floor(Date.now() / 1000);
  if (delta <= 0) return "Window elapsed";
  const hours = Math.floor(delta / 3600);
  const minutes = Math.floor((delta % 3600) / 60);
  return hours ? `${hours}h ${minutes}m remaining` : `${minutes}m remaining`;
}

function ProcessTrace({ promise }: { promise: PromiseRecord }) {
  const states = ["POSTED", "CHALLENGE", "JUDGING", "SETTLED"];
  const status = promise.status;
  const activeIndex = ["COMPILING", "OPEN", "REJECTED", "REJECTED_REFUNDED", "REFUNDABLE_ERROR", "REFUNDED_INVALID"].includes(status) ? 0
    : ["CHALLENGED", "JUDGING", "READY_TO_JUDGE"].includes(status) ? 1
      : status === "RESULT_PENDING" ? 2 : 3;
  return <div className="process-trace" aria-label="Promise process timeline">
    {states.map((label, index) => <div key={label} className={`process-step ${index < activeIndex ? "step-done" : index === activeIndex ? "step-active" : ""}`}>
      <span className="process-node">{index < activeIndex ? <FileCheck2 size={13} /> : String(index + 1).padStart(2, "0")}</span>
      <span><b>{label}</b><small>{index === 0 ? dateLabel(promise.created_at) : index === 1 ? (promise.challenge ? dateLabel(promise.challenge.created_at) : dateLabel(promise.challenge_close_at)) : index === 2 ? (promise.defence_end ? dateLabel(promise.defence_end) : "Awaiting challenge") : (promise.settlement || promise.status).replaceAll("_", " ")}</small></span>
      {index < states.length - 1 && <span className="process-link" />}
    </div>)}
  </div>;
}

function TransactionStatus({ hash, title, onState }: { hash: string; title: string; onState: (hash: string, state: TxState, view?: TxView) => void }) {
  const [view, setView] = useState<TxView | null>(null);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const response = await fetch(`/api/transactions/${hash}`, { cache: "no-store" });
        const result = await response.json() as TxView;
        if (!active || !response.ok) return;
        setView(result);
        onState(hash, result.state, result);
        if (!["FINALIZED_SUCCESS", "FINALIZED_ERROR"].includes(result.state)) timer = setTimeout(poll, 5_000);
      } catch { if (active) timer = setTimeout(poll, 8_000); }
    };
    void poll();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [hash, onState]);
  const state = view?.state ?? "SUBMITTED";
  return <div className="transaction-row">
    <div className="transaction-icon"><ActivityIcon state={state} /></div>
    <div className="transaction-copy"><strong>{title}</strong><a href={`${EXPLORER}/tx/${hash}`} target="_blank" rel="noreferrer">{short(hash, 12, 8)} <ExternalLink size={12} /></a>{view?.error && <small className="error-copy">{view.error}</small>}</div>
    <div className="transaction-state"><b className={`status-tag ${statusTone(state)}`}>{state.replaceAll("_", " ")}</b><small>{view?.appealDeadline ? `Appeal window ends ${dateLabel(view.appealDeadline)}` : state.startsWith("FINALIZED") ? "Finalized" : "Waiting for acceptance"}</small></div>
  </div>;
}

function ActivityIcon({ state }: { state: string }) {
  return state === "FINALIZED_SUCCESS" ? <ShieldCheck size={15} /> : state === "FINALIZED_ERROR" ? <FileClock size={15} /> : <RefreshCw size={14} />;
}

export default function PromiseDetail({ promiseId, proof }: { promiseId: string; proof: Proof }) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [loadError, setLoadError] = useState("");
  const [account, setAccount] = useState("");
  const [busy, setBusy] = useState("");
  const [actionError, setActionError] = useState("");
  const [activity, setActivity] = useState<{ hash: string; title: string; state: TxState; view?: TxView }[]>([]);
  const [challengeForm, setChallengeForm] = useState({ evidence: "", stake: "" });
  const [defence, setDefence] = useState("");
  const board = proof.contracts.BondBoard?.address ?? "";

  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/live", { cache: "no-store" });
      const result = await response.json() as Snapshot;
      setSnapshot(result);
      setLoadError(result.error ?? "");
    } catch (error) { setLoadError(error instanceof Error ? error.message : "StudioNet read failed."); }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), 30_000);
    return () => clearInterval(timer);
  }, [refresh]);

  const promise = snapshot?.promises.find((item) => item.id === promiseId);
  useEffect(() => {
    if (promise && !challengeForm.stake) setChallengeForm((value) => ({ ...value, stake: String(Math.floor(Number(promise.bond_wei) / 4)) }));
  }, [promise, challengeForm.stake]);
  const updateTransactionState = useCallback((hash: string, state: TxState, view?: TxView) => {
    setActivity((items) => items.map((item) => item.hash === hash ? { ...item, state, view } : item));
  }, []);

  async function connect() {
    setActionError("");
    try { setAccount((await walletAccount()).account); }
    catch (error) { setActionError(error instanceof Error ? error.message : "Wallet connection failed."); }
  }

  async function submit(title: string, method: string, args: unknown[], value = 0n) {
    if (!board) { setActionError("BondBoard is not deployed in the current proof manifest."); return; }
    setBusy(method);
    setActionError("");
    try {
      const hash = await write(board, method, args, value);
      setActivity((items) => [{ hash, title, state: "SUBMITTED" }, ...items]);
      setTimeout(() => void refresh(), 5_000);
    } catch (error) { setActionError(error instanceof Error ? error.message : `${title} failed.`); }
    finally { setBusy(""); }
  }

  function parseLines(value: string) {
    return value.split("\n").map((line) => line.trim()).filter(Boolean);
  }

  function challenge(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!promise) return;
    const evidence = parseLines(challengeForm.evidence);
    if (evidence.length < 1 || evidence.length > 3) { setActionError("Add one to three evidence URLs, one per line."); return; }
    if (!/^\d+$/.test(challengeForm.stake) || BigInt(challengeForm.stake) !== BigInt(promise.bond_wei) / 4n) { setActionError("Challenge stake must equal exactly one quarter of the bond."); return; }
    void submit("Challenge promise", "challenge", [promise.id, JSON.stringify(evidence)], BigInt(challengeForm.stake));
  }

  function defend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const evidence = parseLines(defence);
    if (evidence.length < 1 || evidence.length > 2) { setActionError("Add one or two defence URLs, one per line."); return; }
    void submit("Add defence evidence", "defend", [promiseId, JSON.stringify(evidence)]);
  }

  const isPoster = !!account && account.toLowerCase() === promise?.poster?.toLowerCase();
  const transactions = [...(promise?.transactions ?? [])].reverse();

  return <main className="app-shell detail-shell">
    <header className="topbar">
      <Link className="brand-lockup" href="/"><span className="brand-glyph"><i /><i /><i /><i /></span><span>Roadmap Bond</span></Link>
      <nav className="topnav" aria-label="Main navigation"><Link className="nav-active" href="/#ledger">Promise ledger</Link><a href="/#method">How settlement works</a></nav>
      <div className="topbar-tools"><span className="network-chip"><i /> StudioNet <b>61999</b></span><button className="button button-outline" onClick={connect}><Wallet size={15} />{account ? short(account) : "Connect wallet"}</button></div>
    </header>

    <div className="detail-back"><Link href="/"><ArrowLeft size={14} /> Back to ledger</Link><span>RECORD <b>{promiseId}</b></span></div>
    {loadError && <div className="read-notice"><FileClock size={16} /><span><strong>{snapshot?.stale ? "Showing the last available record." : "Live read unavailable."}</strong> {loadError}</span><button onClick={() => void refresh()}>Retry</button></div>}
    {!promise ? <section className="detail-missing"><div className="empty-seal"><Fingerprint size={22} /></div><h1>Promise record not found.</h1><p>This ID is not present in the live StudioNet read or the local proof manifest. The page remains available while deployment is pending.</p><Link className="button button-outline" href="/">Return to promise ledger <ArrowRight size={14} /></Link></section> : <>
      <section className="case-heading">
        <div><div className="case-tags"><span className={`status-tag ${statusTone(promise.status)}`}>{promise.status.replaceAll("_", " ")}</span>{promise.replay && <span className="replay-tag">HISTORICAL REPLAY</span>}</div><h1>{promise.quote}</h1><a className="source-link" href={promise.snapshot_url} target="_blank" rel="noreferrer"><Link2 size={14} /> Exact Wayback snapshot <ExternalLink size={12} /></a></div>
        <div className="case-financial"><span><small>POSTER</small><code>{short(promise.poster)}</code></span><span><small>BOND IN ESCROW</small><b>{promise.bond_wei} <i>wei</i></b></span><span><small>DEADLINE</small><b>{dateLabel(promise.deadline)}</b></span></div>
      </section>

      <ProcessTrace promise={promise} />

      <section className="detail-grid">
        <div className="detail-main">
          <section className="detail-section criteria-section">
            <div className="detail-title"><div><h2>Frozen criteria</h2><p>Each criterion is judged in its own transaction.</p></div><span className="mono-hash">SHA-256 <code>{promise.criteria_hash || "pending compilation"}</code></span></div>
            <ol className="criteria-list">{promise.criteria.length ? promise.criteria.map((criterion, index) => {
              const result = promise.verdicts.find((item) => item.criterion_index === index);
              return <li key={`${index}-${criterion}`}>
                <span className="criterion-number">{String(index + 1).padStart(2, "0")}</span>
                <div className="criterion-body"><p>{criterion}</p>{result && <><blockquote>{result.quote || "No verbatim quote returned."}</blockquote><p className="criterion-reason">{result.reason}</p><div className="criterion-meta"><span className={`status-tag ${statusTone(result.verdict)}`}>{result.verdict.replaceAll("_", " ")}</span><span>Evidence {result.evidence_class}</span><code>SHA-256 {short(result.digest, 12, 8)}</code></div></>}{!result && <span className="criterion-pending">Awaiting judgment</span>}</div>
              </li>;
            }) : <li className="criteria-empty"><span className="criterion-number">—</span><div><p>Criteria have not finalized.</p><small>{promise.compile_reasons.join(" ") || "Compilation is pending or rejected."}</small></div></li>}</ol>
            {promise.not_counted && <div className="not-counted"><span>NOT COUNTED</span><p>{promise.not_counted}</p></div>}
            {promise.compile_reasons.length > 0 && <div className="reason-list"><strong>Compiler notes</strong>{promise.compile_reasons.map((reason, index) => <p key={index}>{reason}</p>)}</div>}
          </section>

          <section className="detail-section evidence-section">
            <div className="detail-title"><div><h2>Evidence bundle</h2><p>Only immutable sources can enter the case.</p></div><span className="evidence-size">30 KB EXTRACT LIMIT</span></div>
            {promise.challenge ? <><div className="evidence-party"><span><Gavel size={14} /> Challenger <code>{short(promise.challenge.challenger)}</code></span><b>Stake {promise.challenge.stake_wei} wei</b></div><ul className="evidence-list">{promise.challenge.evidence.map((url) => <li key={url}><a href={url} target="_blank" rel="noreferrer">{url}<ExternalLink size={12} /></a></li>)}</ul></> : <p className="evidence-empty">No challenge has been recorded.</p>}
            {promise.defence_evidence.length > 0 && <><div className="evidence-party defence-party"><span><ShieldCheck size={14} /> Poster defence</span><b>{promise.defence_evidence.length} source{promise.defence_evidence.length === 1 ? "" : "s"}</b></div><ul className="evidence-list">{promise.defence_evidence.map((url) => <li key={url}><a href={url} target="_blank" rel="noreferrer">{url}<ExternalLink size={12} /></a></li>)}</ul></>}
          </section>

          <section className="detail-section transaction-section">
            <div className="detail-title"><div><h2>Transaction trail</h2><p>Submitted, accepted, and finalized states are distinct.</p></div><span>{transactions.length} recorded</span></div>
            {transactions.length === 0 && activity.length === 0 ? <div className="activity-empty">No transaction hashes are recorded on this promise.</div> : <>
              {transactions.map((item) => <TransactionStatus key={item.hash + item.action} hash={item.hash} title={item.action.replaceAll("_", " ")} onState={updateTransactionState} />)}
              {activity.filter((entry) => !transactions.some((item) => item.hash === entry.hash)).map((entry) => <TransactionStatus key={entry.hash} hash={entry.hash} title={entry.title} onState={updateTransactionState} />)}
            </>}
          </section>
        </div>

        <aside className="detail-aside">
          <section className="detail-section terms-sheet">
            <h2>Windows</h2>
            <div className="term-row"><span>Challenge closes</span><b>{dateLabel(promise.challenge_close_at)}</b><small>{secondsLeft(promise.challenge_close_at)}</small></div>
            <div className="term-row"><span>Defence ends</span><b>{dateLabel(promise.defence_end)}</b><small>{secondsLeft(promise.defence_end)}</small></div>
            <div className="term-row"><span>Judging grace</span><b>{promise.grace_seconds} seconds</b><small>Unjudged criteria become inconclusive.</small></div>
            <div className="appeal-note"><ShieldCheck size={14} /><span>Each accepted transaction carries GenLayer’s native appeal window before its finalized callback.</span></div>
          </section>

          <section className="detail-section action-sheet">
            <div className="detail-title"><div><h2>Next action</h2><p>Contract checks remain authoritative.</p></div><span className="action-indicator"><ActivityIcon state={busy ? "PENDING" : promise.status} /></span></div>
            {promise.status === "OPEN" && <form className="action-form" onSubmit={challenge}><label>Challenge evidence <small>one to three URLs, one per line</small><textarea value={challengeForm.evidence} onChange={(event) => setChallengeForm({ ...challengeForm, evidence: event.target.value })} rows={4} placeholder="https://registry.npmjs.org/package/1.2.3" /></label><label>Challenge stake <small>exactly 25% of bond · wei</small><input inputMode="numeric" value={challengeForm.stake} onChange={(event) => setChallengeForm({ ...challengeForm, stake: event.target.value })} /></label><button className="button button-primary full-width" disabled={!!busy || !board}>{busy === "challenge" ? "Waiting for wallet…" : "Challenge this promise"}</button></form>}
            {promise.status === "CHALLENGED" && isPoster && <form className="action-form" onSubmit={defend}><label>Add defence evidence <small>one or two URLs, up to two total</small><textarea value={defence} onChange={(event) => setDefence(event.target.value)} rows={4} placeholder="https://web.archive.org/web/20240101000000id_/https://…" /></label><button className="button button-primary full-width" disabled={!!busy || !board}>{busy === "defend" ? "Waiting for wallet…" : "Add defence evidence"}</button></form>}
            {promise.status === "OPEN" && <button className="button button-outline full-width" disabled={!!busy || !board || Date.now() / 1000 < promise.challenge_close_at} onClick={() => void submit("Release unchallenged bond", "release", [promise.id])}>Release unchallenged bond</button>}
            {["CHALLENGED", "READY_TO_JUDGE"].includes(promise.status) && <button className="button button-primary full-width" disabled={!!busy || !board || (promise.defence_end > 0 && Date.now() / 1000 < promise.defence_end)} onClick={() => void submit("Judge next criterion", "judge_next", [promise.id])}>{busy === "judge_next" ? "Waiting for validator judgment…" : "Judge next criterion"}</button>}
            {["CHALLENGED", "JUDGING", "READY_TO_JUDGE"].includes(promise.status) && <button className="button button-outline full-width" disabled={!!busy || !board || Date.now() / 1000 < promise.defence_end + Number(promise.grace_seconds)} onClick={() => void submit("Settle after judging grace", "settle_expired", [promise.id])}>Apply elapsed grace fallback</button>}
            {promise.status === "REJECTED" && isPoster && <button className="button button-primary full-width" disabled={!!busy || !board} onClick={() => void submit("Refund rejected promise", "refund_rejected", [promise.id])}>Refund rejected bond</button>}
            {promise.status === "COMPILING" && <button className="button button-outline full-width" disabled={!!busy || !board || Date.now() / 1000 < promise.created_at + Number(promise.grace_seconds)} onClick={() => void submit("Refund expired compilation", "refund_compile_expired", [promise.id])}>Refund expired compilation</button>}
            {!["OPEN", "CHALLENGED", "READY_TO_JUDGE", "JUDGING", "COMPILING", "REJECTED"].includes(promise.status) && <div className="settlement-callout"><span className={`status-tag ${statusTone(promise.status)}`}>{promise.settlement || promise.status}</span><p>{promise.reason || "The promise has reached a final contract state."}</p></div>}
            {actionError && <p className="form-error" role="alert">{actionError}</p>}
            {!account && <p className="form-note">Connect a StudioNet wallet to submit writes. Reading stays public.</p>}
            {account && !isPoster && <p className="form-note">Connected {short(account)}. Poster-only actions stay disabled by contract checks.</p>}
          </section>

          <section className="detail-section payout-sheet">
            <div className="detail-title"><div><h2>Balance movements</h2><p>Finalized outputs stored by BondBoard.</p></div></div>
            {promise.payouts.length ? promise.payouts.map((payout, index) => <div className="payout-row" key={`${index}-${payout.purpose}`}><span><strong>{payout.purpose.replaceAll("_", " ")}</strong><small>{short(payout.recipient)}</small></span><b>{payout.amount_wei} <i>wei</i></b></div>) : <div className="payout-empty">No finalized transfer recorded yet.</div>}
          </section>
        </aside>
      </section>
    </>}

    <footer className="page-footer"><Link href="/">Roadmap Bond</Link><span>Contract state: StudioNet · chain 61999</span><a href={proof.explorer} target="_blank" rel="noreferrer">Explorer <ExternalLink size={12} /></a></footer>
  </main>;
}
