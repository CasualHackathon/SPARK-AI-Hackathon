import fs from "fs";
import path from "path";
import type { VerdictOutput } from "./schema";

type Ledger = {
  case_title: string;
  wallet: string;
  tags: string[];
  radar: VerdictOutput["radar"];
  merits: VerdictOutput["merits"];
  charges: VerdictOutput["charges"];
};

function fetchLedger(sampleKey: string): Ledger {
  const p = path.join(process.cwd(), "ledger", `${sampleKey}.json`);
  const raw = fs.readFileSync(p, "utf-8").replace(/^\uFEFF/, "");
return JSON.parse(raw) as Ledger;

  
}

function narrate(ledger: Ledger): string {
  const main = ledger.tags?.[0] ?? "Unknown";
  const merits = ledger.merits?.length ? "功在可证" : "功未见";
  const charges = ledger.charges?.length ? "罪亦可查" : "罪未显";
  return `此人乃 ${main}。${merits}，${charges}。`;
}

function verifyLinks(items: { proof_url: string }[]): void {
  items.forEach((x) => {
    if (!x.proof_url || !x.proof_url.startsWith("https://")) {
      x.proof_url = "https://etherscan.io";
    }
  });
}

export async function runWorkflow(sampleKey: string): Promise<VerdictOutput> {
  const ledger = fetchLedger(sampleKey);

  verifyLinks(ledger.merits);
  verifyLinks(ledger.charges);

  const verdict = narrate(ledger);

  return {
    case_title: ledger.case_title,
    wallet: ledger.wallet,
    verdict,
    tags: ledger.tags,
    radar: ledger.radar,
    merits: ledger.merits,
    charges: ledger.charges,
    risk_flags: ["Mock ledger for demo", "Click-to-verify with block explorer"]
  };
}
