export type VerdictOutput = {
  case_title: string;
  wallet: string;
  verdict: string;
  tags: string[];
  radar: { wealth: number; holding: number; governance: number; builder: number; degen: number };
  merits: { claim: string; proof_url: string }[];
  charges: { claim: string; proof_url: string }[];
  risk_flags: string[];
};
