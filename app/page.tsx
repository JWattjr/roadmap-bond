import source from "@/deploy/proof.json";
import Ledger from "@/components/ledger";
import type { Proof } from "@/lib/domain";

export default function Page() {
  return <Ledger proof={source as unknown as Proof} />;
}
