/**
 * Minimal Tollex client: discovery, free planning, payment terms, a guarded x402 payment and receipt
 * verification. Uses only public endpoints and the official x402 packages.
 */
import { decodePaymentRequiredHeader, decodePaymentResponseHeader } from "@x402/core/http";
import { ExactEvmScheme } from "@x402/evm";
import { wrapFetchWithPaymentFromConfig } from "@x402/fetch";
import canonicalizeModule from "canonicalize";
import { getAddress, keccak256, recoverTypedDataAddress, toBytes, type Hex, type LocalAccount } from "viem";

export const TOLLEX = process.env.TOLLEX_URL ?? "https://api.tollex.org";

/**
 * The payment rails Tollex accepts. Pin them: a 402 asking for any other network, asset or a higher amount
 * than your ceiling is refused before anything is signed.
 */
export const RAILS = {
  /** USDC on Base mainnet: an @x402 default asset, the shortest path for most x402 wallets. */
  base: { network: "eip155:8453", asset: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", symbol: "USDC", explorer: "https://base.blockscout.com/tx/" },
  /** USDG on Robinhood Chain mainnet (not an @x402 default asset: allowed explicitly below). */
  robinhood: { network: "eip155:4663", asset: "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168", symbol: "USDG", explorer: "https://robinhoodchain.blockscout.com/tx/" },
} as const;
export type RailName = keyof typeof RAILS;
export const rail = (name: string): (typeof RAILS)[RailName] => {
  const r = RAILS[name as RailName];
  if (!r) throw new Error(`unknown rail "${name}" (use: ${Object.keys(RAILS).join(", ")})`);
  return r;
};

/** Spend policy enforced locally, before any signature: per call, per session, allowed rails. */
export class SpendPolicy {
  private spent = 0n;
  constructor(readonly maxPerCall: bigint, readonly maxPerSession: bigint, readonly rails: readonly RailName[]) {}
  check(r: (typeof RAILS)[RailName], amount: bigint): void {
    if (!this.rails.some((n) => RAILS[n].network === r.network)) throw new Error(`rail ${r.network} not allowed by policy`);
    if (amount > this.maxPerCall) throw new Error(`price ${amount} above the per-call ceiling ${this.maxPerCall}`);
    if (this.spent + amount > this.maxPerSession) throw new Error(`price ${amount} would exceed the session budget (${this.spent}/${this.maxPerSession} spent)`);
  }
  record(amount: bigint): void {
    this.spent += amount;
  }
}

const json = async <T>(r: Response): Promise<T> => {
  if (!r.ok && r.status !== 402) throw new Error(`${r.url}: HTTP ${r.status} ${(await r.text()).slice(0, 200)}`);
  return (await r.json()) as T;
};

/** 1. Discovery: the service descriptor names the network, asset and every endpoint. */
export async function discover() {
  return json<{ name: string; payment: { networks: string[]; assets: { address: string; symbol: string }[] }; capabilities: { count: number }; endpoints: Record<string, string> }>(
    await fetch(`${TOLLEX}/.well-known/tollex.json`),
  );
}

/** 2. Free planning: which capability fits the need, and what it costs. Never spends. */
export async function plan(need: string, input?: unknown, maxCost?: bigint) {
  const r = await fetch(`${TOLLEX}/v1/resolve`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ need, ...(input ? { input } : {}), ...(maxCost ? { constraints: { maxCost: maxCost.toString() } } : {}) }),
  });
  return json<{ plan: { selected: { toolId: string } | null; eligible: number; candidates: number } }>(r);
}

/** 3. Payment terms: an unpaid call returns HTTP 402 with the exact, authoritative terms (one option per rail). */
export async function terms(path: string, init: RequestInit, r: (typeof RAILS)[RailName]) {
  const res = await fetch(`${TOLLEX}${path}`, init);
  if (res.status !== 402) throw new Error(`expected 402 payment terms, got ${res.status}${res.status === 503 ? " (paid calls paused: gas spike; retry later)" : ""}`);
  const pr = decodePaymentRequiredHeader(res.headers.get("payment-required") ?? "");
  const option = pr.accepts.find((a) => a.network === r.network && getAddress(a.asset) === getAddress(r.asset));
  if (!option) throw new Error(`no ${r.symbol} option on ${r.network} in the challenge (offered: ${pr.accepts.map((a) => a.network).join(", ")})`);
  return { amount: BigInt(option.amount), payTo: option.payTo, option, challenge: pr };
}

/**
 * 4. Pay and call on ONE pinned rail, only within the policy. The payer signs an EIP-3009 authorization for
 * exactly the quoted amount; the facilitator settles it on chain; Tollex confirms the settlement on chain
 * and returns the result with a signed receipt.
 */
export async function buy(account: LocalAccount, path: string, init: RequestInit, r: (typeof RAILS)[RailName], policy: SpendPolicy) {
  let charged = 0n;
  const fetchWithPayment = wrapFetchWithPaymentFromConfig(fetch, {
    schemes: [{ network: r.network as `${string}:${string}`, client: new ExactEvmScheme(account) }],
    // Only this asset on this network, capped per payment (USDG must be allowed explicitly; USDC is a default).
    spendControls: { allowedAssets: [{ network: r.network as `${string}:${string}`, asset: r.asset, maxAmountPerPayment: policy.maxPerCall.toString() }] },
    paymentRequirementsSelector: (_v, accepts) => {
      const ok = accepts.find((a) => a.network === r.network && getAddress(a.asset) === getAddress(r.asset));
      if (!ok) throw new Error(`refusing to pay: no ${r.symbol} option on ${r.network}`);
      policy.check(r, BigInt(ok.amount));
      charged = BigInt(ok.amount);
      return ok;
    },
  });
  const res = await fetchWithPayment(`${TOLLEX}${path}`, init);
  const header = res.headers.get("payment-response");
  const settlement = header ? decodePaymentResponseHeader(header) : null;
  if (res.status === 200) policy.record(charged);
  const body = await res.json().catch(() => null);
  // 402 after paying = rejected before anything was broadcast (e.g. insufficient balance): nothing moved.
  return { status: res.status, body, settlement, explorer: settlement?.transaction ? `${r.explorer}${settlement.transaction}` : null };
}

/** If a response was lost, ask for the operation's state instead of paying again. */
export async function operation(operationId: string) {
  return json(await fetch(`${TOLLEX}/tollex/operations/${encodeURIComponent(operationId)}`));
}

export interface SignedReceipt { body: Record<string, unknown> & { receiptId: string; version: number; issuedAt: number }; contentHash: Hex; signature: Hex; signer: string }

/**
 * 5. Verify a receipt: contentHash = keccak256(RFC 8785 canonical JSON of the body); the EIP-712 signer of
 * {version, receiptId, contentHash, issuedAt} must be an ACTIVE key published by Tollex.
 */
export async function verifyReceipt(receipt: SignedReceipt) {
  // RFC 8785 (JCS) canonical JSON; "canonicalize" is CommonJS, so unwrap its export in either module mode.
  const canonicalize = ((canonicalizeModule as unknown as { default?: (v: unknown) => string }).default ?? canonicalizeModule) as unknown as (v: unknown) => string;
  const contentHash = keccak256(toBytes(canonicalize(receipt.body)));
  const signer = await recoverTypedDataAddress({
    domain: { name: "Tollex Execution Receipt", version: "1" },
    types: { ExecutionReceipt: [{ name: "version", type: "uint256" }, { name: "receiptId", type: "string" }, { name: "contentHash", type: "bytes32" }, { name: "issuedAt", type: "uint256" }] },
    primaryType: "ExecutionReceipt",
    message: { version: BigInt(receipt.body.version), receiptId: receipt.body.receiptId, contentHash, issuedAt: BigInt(receipt.body.issuedAt) },
    signature: receipt.signature,
  });
  const keys = await json<{ keys: { address: string; status: string }[] }>(await fetch(`${TOLLEX}/.well-known/tollex-receipt-keys`));
  const active = keys.keys.some((k) => k.status === "active" && getAddress(k.address) === signer);
  return { valid: contentHash === receipt.contentHash && active, contentHashMatches: contentHash === receipt.contentHash, signer, signerIsActiveTollexKey: active };
}

export async function getReceipt(receiptId: string) {
  return json<SignedReceipt>(await fetch(`${TOLLEX}/tollex/receipts/${encodeURIComponent(receiptId)}`));
}
