export const runtime = "nodejs";

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";

import { runWorkflow } from "@/agent/workflow";

const execFileAsync = promisify(execFile);

function isEthAddress(s: string) {
  return /^0x[a-fA-F0-9]{40}$/.test(s);
}

function ensureArray(x: any) {
  return Array.isArray(x) ? x : [];
}

// 把 workflow 里那些“老的 mock 提示语”清掉，避免前端把它当回退
function stripLegacyMockFlags(flags: string[]) {
  const kill = [
    "mock ledger for demo",
    "click-to-verify with block explorer",
  ];
  return flags.filter((s) => {
    const t = (s ?? "").toLowerCase();
    return !kill.some((k) => t.includes(k));
  });
}

async function runSpoonOS(sampleKey: string, wallet: string) {
  const root = process.cwd();
  const py = path.join(root, "spoon-env", "Scripts", "python.exe");
  const script = path.join(root, "spoonos", "judge_graph.py");

  const { stdout } = await execFileAsync(py, [script, sampleKey, wallet], {
    cwd: root,
    windowsHide: true,
    maxBuffer: 1024 * 1024,
  });

  return JSON.parse(stdout);
}

async function fetchRecentProofHashes(wallet: string, limit = 4) {
  const apiKey = (process.env.ETHERSCAN_API_KEY ?? "").trim();
  if (!apiKey) return [];

  async function call(action: "txlist" | "tokentx") {
    const url =
      `https://api.etherscan.io/v2/api?chainid=1&module=account&action=${action}` +
      `&address=${encodeURIComponent(wallet)}` +
      `&startblock=0&endblock=99999999&page=1&offset=${limit}&sort=desc` +
      `&apikey=${encodeURIComponent(apiKey)}`;

    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) return [];

    const j: any = await r.json();
    if (j.status !== "1" || !Array.isArray(j.result)) return [];

    return j.result
      .map((x: any) => x?.hash)
      .filter((h: any) => typeof h === "string" && h.startsWith("0x"));
  }

  const normal = await call("txlist");
  if (normal.length >= limit) return normal;

  const token = await call("tokentx");
  const merged = [...normal, ...token].filter(Boolean);

  return Array.from(new Set(merged)).slice(0, limit);
}

function applyHashesToProofLinks(data: any, hashes: string[]) {
  data.merits = ensureArray(data.merits);
  data.charges = ensureArray(data.charges);

  for (let i = 0; i < Math.min(3, hashes.length); i++) {
    if (data.merits[i]) data.merits[i].proof_url = `https://etherscan.io/tx/${hashes[i]}`;
  }

  if (hashes[3] && data.charges[0]) {
    data.charges[0].proof_url = `https://etherscan.io/tx/${hashes[3]}`;
  }
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const sample = searchParams.get("sample") ?? "sampleA";
  const wallet = (searchParams.get("wallet") ?? "").trim();

  let data: any;

  // 先 SpoonOS，失败才 workflow，但注意：workflow 自带的 mock flags 不能干扰前端
  try {
    data = await runSpoonOS(sample, wallet);
  } catch {
    data = await runWorkflow(sample);
    data.risk_flags = stripLegacyMockFlags(ensureArray(data.risk_flags));
    // 注意：这里不要写 "Fallback:"，否则你前端会误判
    data.risk_flags.unshift("SpoonOS graph unavailable (mock workflow used for stability).");
  }

  data.risk_flags = stripLegacyMockFlags(ensureArray(data.risk_flags));

  // 没填/不合法地址：明确回退（这才该触发 ⚠）
  if (!isEthAddress(wallet)) {
    data.risk_flags.unshift("Fallback: no valid wallet provided - showing sample proof links (mock).");
    return Response.json(data);
  }

  // 合法地址：尝试拉 live tx
  const hashes = await fetchRecentProofHashes(wallet, 4);

  if (hashes.length > 0) {
    applyHashesToProofLinks(data, hashes);
    // live 成功：确保 flags 不含任何“mock/回退”提示
    data.risk_flags = stripLegacyMockFlags(ensureArray(data.risk_flags))
      .filter((s) => !String(s).toLowerCase().startsWith("fallback:"));
    data.risk_flags.unshift("Live proof: Etherscan API v2 (ETH mainnet) - proof links reflect THIS wallet.");
  } else {
    // live 失败：这才是 ⚠
    data.risk_flags.unshift(
      "Fallback: live tx unavailable for this address - showing sample proof links for demo stability."
    );
  }

  return Response.json(data);
}