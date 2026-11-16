export type TxState = "SUBMITTED" | "PENDING" | "ACCEPTED" | "FINALIZED_SUCCESS" | "FINALIZED_ERROR";

export type Verdict = {
  criterion_index: number;
  criterion: string;
  verdict: "MET" | "NOT_MET" | "INSUFFICIENT_EVIDENCE";
  quote: string;
  reason: string;
  digest: string;
  evidence_class: string;
  recorded_at: number;
};

export type Challenge = {
  challenger: string;
  stake_wei: string;
  evidence: string[];
  created_at: number;
};

export type Payout = {
  purpose: string;
  recipient: string;
  amount_wei: string;
  state: "FINALIZED";
};

export type PromiseRecord = {
  id: string;
  poster: string;
  snapshot_url: string;
  quote: string;
  deadline: number;
  bond_wei: string;
  challenge_stake_wei: string;
  challenge_window_seconds: string;
  defence_window_seconds: string;
  grace_seconds: string;
  created_at: number;
  challenge_close_at: number;
  defence_end: number;
  replay: boolean;
  status: string;
  criteria: string[];
  criteria_hash: string;
  not_counted: string;
  compile_reasons: string[];
  challenge: Challenge | null;
  defence_evidence: string[];
  verdicts: Verdict[];
  payouts: Payout[];
  next_criterion: number;
  settlement: string;
  reason: string;
  transactions: { action: string; hash: string }[];
};

export type Snapshot = {
  promises: PromiseRecord[];
  readAt: string;
  network: "StudioNet";
  chainId: 61999;
  source: "live" | "recorded";
  error?: string;
  stale?: boolean;
  staleSince?: string;
};

export type Proof = {
  network: string;
  chainId: number;
  explorer: string;
  rpc: string;
  releaseStatus: string;
  approvedTotalWei: number;
  contracts: Record<string, { address: string; source: string; sha256: string }>;
  transactions: Record<string, string>;
  cases: Record<string, Record<string, unknown>>;
  probeResults?: Record<string, unknown>;
  sourceCommit?: string | null;
  appUrl?: string | null;
  fixturesRepo?: string;
};

export type TxView = {
  hash: string;
  state: TxState;
  children: string[];
  appealDeadline: number | null;
  error: string | null;
};

export function transactionState(r: Record<string, unknown>): TxState {
  const status = String(r.status_name ?? r.status ?? "SUBMITTED");
  if (status === "FINALIZED" || status === "7") {
    const consensus = r.consensus_data as { leader_receipt?: { execution_result?: string }[] } | undefined;
    const execution = String(r.txExecutionResultName ?? consensus?.leader_receipt?.[0]?.execution_result ?? "");
    return (["SUCCESS", "FINISHED_WITH_RETURN"].includes(execution) ||
      (r.value_credited === true && String(r.type) === "0" && !r.consensus_data)) &&
      !["MAJORITY_DISAGREE", "DISAGREE"].includes(String(r.result_name))
      ? "FINALIZED_SUCCESS"
      : "FINALIZED_ERROR";
  }
  return status === "ACCEPTED" || status === "6" ? "ACCEPTED" : status === "SUBMITTED" ? "SUBMITTED" : "PENDING";
}

export const short = (value: string, left = 8, right = 6) =>
  value.length > left + right + 1 ? `${value.slice(0, left)}…${value.slice(-right)}` : value;
