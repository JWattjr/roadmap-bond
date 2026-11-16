import { recordedPromises, snapshot } from "@/lib/server-chain";
import type { Snapshot } from "@/lib/domain";

export const dynamic = "force-dynamic";

const FRESH_MS = 60_000;
let lastGood: { at: number; value: Snapshot } | null = null;

export async function GET() {
  const headers = { "Cache-Control": "no-store" };
  if (lastGood && Date.now() - lastGood.at < FRESH_MS) {
    return Response.json(lastGood.value, { headers });
  }
  try {
    const value = await snapshot();
    lastGood = { at: Date.now(), value };
    return Response.json(value, { headers });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Live reads are unavailable.";
    if (lastGood) {
      return Response.json({
        ...lastGood.value,
        stale: true,
        staleSince: new Date(lastGood.at).toISOString(),
        error: `Live read unavailable (${message}). Showing the last good read.`,
      }, { headers });
    }
    return Response.json({
      promises: recordedPromises(),
      readAt: new Date().toISOString(),
      network: "StudioNet",
      chainId: 61999,
      source: "recorded",
      stale: true,
      error: `Live read unavailable (${message}). Showing the recorded proof manifest.`,
    } satisfies Snapshot, { headers });
  }
}
