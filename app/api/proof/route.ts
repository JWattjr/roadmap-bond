import { recorded } from "@/lib/server-chain";

export async function GET() {
  return Response.json(recorded, {
    headers: { "Cache-Control": "public, s-maxage=30, stale-while-revalidate=30" },
  });
}
