import source from "@/deploy/proof.json";
import PromiseDetail from "@/components/promise-detail";
import type { Proof } from "@/lib/domain";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PromiseDetail promiseId={decodeURIComponent(id)} proof={source as unknown as Proof} />;
}
