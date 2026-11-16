import { createClient, decodeLocalnetTransaction } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionHashVariant, type TransactionHash } from "genlayer-js/types";
import type { Proof, PromiseRecord, Snapshot, TxView } from "./domain";
import { transactionState } from "./domain";
import source from "@/deploy/proof.json";

export const recorded = source as unknown as Proof;
const client = createClient({ chain: studionet, endpoint: "https://studio.genlayer.com/api" });
const cache = new Map<string, { at: number; value: unknown }>();
const pending = new Map<string, Promise<unknown>>();

async function memo<T>(key: string, fn: () => Promise<T>, ttl = 60_000): Promise<T> {
  const old = cache.get(key);
  if (old && Date.now() - old.at < ttl) return old.value as T;
  const running = pending.get(key);
  if (running) return running as Promise<T>;
  const task = fn().then((value) => {
    cache.set(key, { at: Date.now(), value });
    return value;
  }).finally(() => pending.delete(key));
  pending.set(key, task);
  return task;
}

function decode<T>(value: unknown): T {
  if (typeof value === "string" && /^[\[{]/.test(value.trim())) return JSON.parse(value) as T;
  return value as T;
}

export function recordedPromises(): PromiseRecord[] {
  return Object.values(recorded.cases ?? {})
    .map((item) => item.promise)
    .filter((item): item is PromiseRecord => Boolean(item && typeof item === "object" && "id" in item));
}

export async function read<T>(method: string, args: unknown[] = []): Promise<T> {
  const address = recorded.contracts.BondBoard?.address;
  if (!address) throw Error("BondBoard is not deployed in the current proof manifest.");
  return memo(`board:${method}:${JSON.stringify(args)}`, async () => {
    const result = await client.readContract({
      address: address as `0x${string}`,
      functionName: method,
      args: args as never[],
      transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
    });
    return decode<T>(result);
  });
}

export async function snapshot(): Promise<Snapshot> {
  const promises = await read<PromiseRecord[]>("get_promises", [0, 50]);
  return {
    promises: (promises ?? []).slice().reverse(),
    readAt: new Date().toISOString(),
    network: "StudioNet",
    chainId: 61999,
    source: "live",
  };
}

export async function transaction(hash: string): Promise<TxView> {
  if (!/^0x[0-9a-fA-F]{64}$/.test(hash)) throw Error("Transaction hash is malformed.");
  return memo(`tx:${hash}`, async () => {
    const raw = await client.request({ method: "eth_getTransactionByHash", params: [hash as TransactionHash] });
    if (!raw) return { hash, state: "SUBMITTED", children: [], appealDeadline: null, error: null };
    const receipt = decodeLocalnetTransaction(raw as never) as unknown as Record<string, unknown>;
    const state = transactionState(receipt);
    let appealDeadline: number | null = null;
    if (state === "ACCEPTED") {
      try {
        const window = Number(await client.request({ method: "sim_getFinalityWindowTime" as never }));
        const starts = Number(receipt.timestamp_awaiting_finalization ?? 0);
        if (starts > 0 && window > 0 && receipt.leader_only === false && receipt.appealed !== true) {
          appealDeadline = starts + Number(receipt.appeal_processing_time ?? 0) + window * 0.8 ** Number(receipt.appeal_failed ?? 0);
        }
      } catch {
        appealDeadline = null;
      }
    }
    const leader = (receipt.consensus_data as { leader_receipt?: { result?: { payload?: { readable?: string } }; genvm_result?: { stderr?: string } }[] } | undefined)?.leader_receipt?.[0];
    return {
      hash,
      state,
      children: (receipt.triggered_transactions as string[]) ?? [],
      appealDeadline,
      error: state === "FINALIZED_ERROR" ? leader?.result?.payload?.readable ?? leader?.genvm_result?.stderr ?? "Open the transaction receipt for the execution error." : null,
    };
  }, 8_000);
}
