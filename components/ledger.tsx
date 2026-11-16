"use client";

import { Activity, ArrowDownLeft, ArrowRight, ArrowUpRight, ExternalLink, FileClock, Fingerprint, RefreshCw, ShieldCheck, Wallet } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { Proof, PromiseRecord, Snapshot, TxState } from "@/lib/domain";
import { short } from "@/lib/domain";
import { walletAccount, write } from "@/lib/wallet";

const EXPLORER = "https://explorer-studio.genlayer.com";

function statusTone(status: string) {
  if (["OPEN", "KEPT", "RELEASED", "REJECTED_REFUNDED"].includes(status)) return "tone-good";
  if (["COMPILING", "CHALLENGED", "JUDGING", "READY_TO_JUDGE", "RESULT_PENDING", "RELEASE_PENDING", "REJECT_REFUND_PENDING"].includes(status)) return "tone-wait";
  if (["BROKEN", "REJECTED", "REFUNDABLE_ERROR", "REFUNDED_INVALID"].includes(status)) return "tone-bad";
  return "tone-neutral";
}

function formattedDate(seconds: number) {
  if (!seconds) return "Not recorded";
  return new Date(seconds * 1000).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function targetName(snapshotUrl: string) {
  const marker = "/id_/";
  const index = snapshotUrl.indexOf(marker);
  if (index < 0) return "Archived source";
  try { return new URL(snapshotUrl.slice(index + marker.length)).hostname; }
  catch { return "Archived source"; }
}

function FlowStrip() {
  return <section className="route-sheet" aria-label="Settlement routes">
    <div className="route-sheet-head"><strong>Settlement routes</strong><span>CODE OWNS PAYOUT</span></div>
    <div className="route-line route-kept"><span className="route-port">A</span><span className="route-name">Every criterion MET</span><ArrowRight size={15} /><span className="route-recipient">Poster <b>bond + stake</b></span></div>
    <div className="route-line route-broken"><span className="route-port">B</span><span className="route-name">Any criterion NOT_MET</span><ArrowRight size={15} /><span className="route-recipient">Challenger <b>bond + stake</b></span></div>
    <div className="route-line route-unproven"><span className="route-port">C</span><span className="route-name">Evidence inconclusive</span><ArrowRight size={15} /><span className="route-recipient">Both <b>refund</b></span></div>
    <div className="route-sheet-foot"><span>Validators return verdicts only.</span><span>Finalized transfers are recorded on-chain.</span></div>
  </section>;
}

function PromiseRow({ item, index }: { item: PromiseRecord; index: number }) {
  return <Link className="promise-row" href={`/promise/${encodeURIComponent(item.id)}`}>
    <span className="row-id"><small>RECORD</small><b>{String(index + 1).padStart(2, "0")}</b></span>
    <span className="promise-copy"><strong>{item.quote || "Quote not available"}</strong><small><span>{targetName(item.snapshot_url)}</span><i>·</i><span>{item.id}</span>{item.replay && <em>HISTORICAL REPLAY</em>}</small></span>
    <span className="row-deadline"><small>DEADLINE</small><b>{formattedDate(item.deadline)}</b></span>
    <span className="row-bond"><small>BOND</small><b>{item.bond_wei} <i>wei</i></b></span>
    <span className={`status-tag ${statusTone(item.status)}`}>{item.status.replaceAll("_", " ")}</span>
    <ArrowUpRight className="row-open" size={16} />
  </Link>;
}

function TransactionMonitor({ hash, title, onState }: { hash: string; title: string; onState: (hash: string, state: TxState) => void }) {
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const response = await fetch(`/api/transactions/${hash}`, { cache: "no-store" });
        const result = await response.json() as { state: TxState };
        if (!active || !response.ok) return;
        onState(hash, result.state);
        if (!["FINALIZED_SUCCESS", "FINALIZED_ERROR"].includes(result.state)) timer = setTimeout(poll, 5_000);
      } catch { if (active) timer = setTimeout(poll, 8_000); }
    };
    void poll();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [hash, onState]);
  return <span>{title}</span>;
}

export default function Ledger({ proof }: { proof: Proof }) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [loadError, setLoadError] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [account, setAccount] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [activity, setActivity] = useState<{ hash: string; title: string; state: TxState }[]>([]);
  const [form, setForm] = useState({ snapshot: "", quote: "", deadline: "", bond: "40" });
  const board = proof.contracts.BondBoard?.address ?? "";

  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/live", { cache: "no-store" });
      const value = await response.json() as Snapshot;
      setSnapshot(value);
      setLoadError(value.error ?? "");
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "StudioNet read failed.");
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), 30_000);
    return () => clearInterval(timer);
  }, [refresh]);

  const promises = snapshot?.promises ?? [];
  const visible = useMemo(() => filter === "ALL" ? promises : promises.filter((item) => filter === "OPEN" ? item.status === "OPEN" : item.status !== "OPEN"), [promises, filter]);
  const onState = useCallback((hash: string, state: TxState) => {
    setActivity((items) => items.map((item) => item.hash === hash ? { ...item, state } : item));
  }, []);

  async function connect() {
    setActionError("");
    try { setAccount((await walletAccount()).account); }
    catch (error) { setActionError(error instanceof Error ? error.message : "Wallet connection failed."); }
  }

  async function postPromise(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError("");
    if (!board) { setActionError("BondBoard is not deployed in the current proof manifest."); return; }
    const deadline = Math.floor(new Date(form.deadline).getTime() / 1000);
    if (!Number.isFinite(deadline) || deadline < Date.now() / 1000 + 3600) { setActionError("Choose a deadline at least 60 minutes from now."); return; }
    if (form.quote.trim().length < 20 || form.quote.trim().length > 300) { setActionError("The archived promise quote must contain 20 to 300 characters."); return; }
    if (!/^https:\/\/web\.archive\.org\/web\/\d{14}id_\/https:\/\//.test(form.snapshot.trim())) { setActionError("Use an exact Wayback id_ snapshot URL."); return; }
    if (!/^\d+$/.test(form.bond) || BigInt(form.bond) <= 0n) { setActionError("Enter a positive bond in wei."); return; }
    setBusy(true);
    try {
      const hash = await write(board, "post", [form.snapshot.trim(), form.quote.trim(), deadline], BigInt(form.bond));
      setActivity((items) => [{ hash, title: "Post promise", state: "SUBMITTED" }, ...items]);
      setForm({ snapshot: "", quote: "", deadline: "", bond: "40" });
      setTimeout(() => void refresh(), 5_000);
    } catch (error) { setActionError(error instanceof Error ? error.message : "Promise submission failed."); }
    finally { setBusy(false); }
  }

  return <main className="app-shell">
    <header className="topbar">
      <Link className="brand-lockup" href="/" aria-label="Roadmap Bond home"><span className="brand-glyph"><i /><i /><i /><i /></span><span>Roadmap Bond</span></Link>
      <nav className="topnav" aria-label="Main navigation"><a className="nav-active" href="#ledger">Promise ledger</a><a href="#method">How settlement works</a></nav>
      <div className="topbar-tools">
        <span className="network-chip"><i /> StudioNet <b>61999</b></span>
        <span className={`read-state ${snapshot?.source === "live" && !snapshot.stale ? "read-live" : "read-recorded"}`}><i />{snapshot?.source === "live" && !snapshot.stale ? "Live read" : "Recorded view"}</span>
        <button className="button button-outline" onClick={connect}><Wallet size={15} />{account ? short(account) : "Connect wallet"}</button>
      </div>
    </header>

    <section className="opening">
      <div className="opening-copy">
        <h1>A promise enters escrow.</h1>
        <p>Public roadmap words become frozen criteria, evidence, and a bond that settles after validators judge.</p>
        <div className="opening-actions"><a className="button button-primary" href="#post"><span>Post a promise</span><ArrowDownLeft size={15} /></a><a className="plain-link" href="#ledger">Inspect the ledger <ArrowRight size={14} /></a></div>
        <div className="read-proof"><Activity size={14} /><span>{snapshot?.source === "live" && !snapshot.stale ? `Read from StudioNet at ${new Date(snapshot.readAt).toLocaleTimeString()}` : "Recorded proof is separate from the current chain read"}</span></div>
      </div>
      <FlowStrip />
    </section>

    <section className="ledger-section" id="ledger">
      <div className="section-heading">
        <div><h2>Promise ledger</h2><p>One archived sentence per record. Follow its state to a finalized outcome.</p></div>
        <div className="ledger-tools"><button className={filter === "ALL" ? "filter-active" : ""} onClick={() => setFilter("ALL")}>All <b>{promises.length}</b></button><button className={filter === "OPEN" ? "filter-active" : ""} onClick={() => setFilter("OPEN")}>Open <b>{promises.filter((item) => item.status === "OPEN").length}</b></button><button className={filter === "RESOLVED" ? "filter-active" : ""} onClick={() => setFilter("RESOLVED")}>Resolved <b>{promises.filter((item) => item.status !== "OPEN").length}</b></button><button className="refresh-button" onClick={() => void refresh()} aria-label="Refresh promise ledger"><RefreshCw size={15} /></button></div>
      </div>
      {loadError && <div className="read-notice"><FileClock size={16} /><span><strong>{snapshot?.stale ? "Showing the last available record." : "Live read unavailable."}</strong> {loadError}</span><button onClick={() => void refresh()}>Retry</button></div>}
      <div className="ledger-table">
        <div className="ledger-head"><span>ROUTE / PROMISE</span><span>DEADLINE</span><span>ESCROW</span><span>STATE</span></div>
        {visible.map((item, index) => <PromiseRow key={item.id} item={item} index={index} />)}
        {visible.length === 0 && <div className="empty-ledger"><div className="empty-seal"><Fingerprint size={22} /></div><div><strong>{promises.length === 0 ? "No promise records yet" : "No records in this view"}</strong><p>{promises.length === 0 ? "A posted promise will appear here after its transaction is accepted. The current workspace has no deployed cases in its proof manifest." : "Change the filter to see other promise states."}</p></div></div>}
      </div>
      <div className="table-footer"><span>{promises.length} promise records</span><span>{snapshot?.source === "live" && !snapshot.stale ? "Latest finalized chain view" : "Recorded proof manifest"}</span></div>
    </section>

    <section className="lower-grid">
      <section className="method-sheet" id="method">
        <h2>The evidence path</h2>
        <div className="method-rail">
          <div className="method-step"><span className="method-node">01</span><div><strong>Archive fixes the words</strong><p>Exact timestamped capture, exact quote, and CDX proof.</p></div></div>
          <div className="method-step"><span className="method-node">02</span><div><strong>Validators freeze the criteria</strong><p>One to three observable checks, hashed before the challenge window.</p></div></div>
          <div className="method-step"><span className="method-node">03</span><div><strong>Code routes the funds</strong><p>Native transfers happen through finalized contract calls.</p></div></div>
        </div>
      </section>

      <section className="post-sheet" id="post">
        <div className="sheet-heading"><div><h2>Post a promise</h2><p>Lock a bond against your own archived words.</p></div><span className="sheet-mark"><ShieldCheck size={17} /></span></div>
        <form className="post-form" onSubmit={postPromise}>
          <label>Exact Wayback snapshot URL<input value={form.snapshot} onChange={(event) => setForm({ ...form, snapshot: event.target.value })} placeholder="https://web.archive.org/web/20200101000000id_/https://…" /></label>
          <label>Promise sentence <small>20–300 characters, verbatim</small><textarea value={form.quote} onChange={(event) => setForm({ ...form, quote: event.target.value })} rows={3} placeholder="Paste one sentence from the archived page." /></label>
          <div className="form-pair"><label>Deadline<input type="datetime-local" value={form.deadline} onChange={(event) => setForm({ ...form, deadline: event.target.value })} /></label><label>Bond <small>wei</small><input inputMode="numeric" value={form.bond} onChange={(event) => setForm({ ...form, bond: event.target.value })} /></label></div>
          {actionError && <p className="form-error" role="alert">{actionError}</p>}
          <button className="button button-primary full-width" disabled={busy || !board}>{busy ? "Waiting for wallet signature…" : board ? "Review and publish" : "Contract not deployed"}</button>
          <p className="form-note"><ShieldCheck size={13} /> Invalid posts receive a recorded refund path. Live writes require a StudioNet wallet.</p>
        </form>
      </section>
    </section>

    <section className="proof-strip">
      <div><h2>Release record</h2><p>Only finalized addresses and transactions count as proof.</p></div>
      <div className="proof-stats"><span><small>RELEASE</small><b className={proof.releaseStatus === "DEPLOYED" ? "tone-good-text" : "tone-wait-text"}>{proof.releaseStatus.replaceAll("_", " ")}</b></span><span><small>RECORDED TXNS</small><b>{Object.keys(proof.transactions ?? {}).length}</b></span><span><small>APPROVED GROSS</small><b>{proof.approvedTotalWei.toLocaleString()} wei</b></span></div>
      <div className="proof-contracts">{Object.entries(proof.contracts ?? {}).map(([name, item]) => <a key={name} href={`${EXPLORER}/address/${item.address}`} target="_blank" rel="noreferrer"><span><small>{name}</small><code>{short(item.address)}</code></span><ExternalLink size={13} /></a>)}</div>
      <a className="manifest-link" href="/api/proof" target="_blank" rel="noreferrer">Open proof manifest <ExternalLink size={12} /></a>
    </section>

    <section className="activity-sheet">
      <div className="section-heading"><div><h2>Wallet activity</h2><p>Submitted writes are tracked until finality.</p></div><span className="activity-count">{activity.length} local</span></div>
      {activity.length === 0 ? <div className="activity-empty">No writes in this browser session. Reading the ledger does not need a wallet.</div> : activity.map((item) => <div className="activity-row" key={item.hash}><span><TransactionMonitor hash={item.hash} title={item.title} onState={onState} /><a href={`${EXPLORER}/tx/${item.hash}`} target="_blank" rel="noreferrer">{short(item.hash)} <ExternalLink size={11} /></a></span><b className={`status-tag ${item.state.startsWith("FINALIZED") ? item.state === "FINALIZED_SUCCESS" ? "tone-good" : "tone-bad" : "tone-wait"}`}>{item.state.replaceAll("_", " ")}</b></div>)}
    </section>

    <footer className="page-footer"><Link href="/">Roadmap Bond</Link><span>Historical replay is a demo path. StudioNet contract state is shown when available.</span><a href={proof.explorer} target="_blank" rel="noreferrer">GenLayer Explorer <ExternalLink size={12} /></a></footer>
  </main>;
}
