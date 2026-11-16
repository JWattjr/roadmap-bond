import { transaction } from "@/lib/server-chain";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, { params }: { params: Promise<{ hash: string }> }) {
  try {
    const { hash } = await params;
    return Response.json(await transaction(hash), { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Transaction could not be read." }, { status: 400 });
  }
}
