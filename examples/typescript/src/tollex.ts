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
export const NETWORK = "eip155:4663"; // Robinhood Chain mainnet
export const USDG = "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168"; // 6 decimals

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

/** 3. Payment terms: an unpaid call returns HTTP 402 with the exact, authoritative terms. */
export async function terms(toolId: string, input: unknown) {
  const r = await fetch(`${TOLLEX}/tools/${toolId}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(input) });
  if (r.status !== 402) throw new Error(`expected 402 payment terms, got ${r.status}${r.status === 503 ? " (paid calls paused: gas spike; retry later)" : ""}`);
  const pr = decodePaymentRequiredHeader(r.headers.get("payment-required") ?? "");
  const option = pr.accepts.find((a) => a.network === NETWORK && getAddress(a.asset) === getAddress(USDG));
  if (!option) throw new Error("no USDG payment option on Robinhood Chain in the challenge");
  return { url: `${TOLLEX}/tools/${toolId}`, amount: BigInt(option.amount), payTo: option.payTo, option, challenge: pr };
}

/**
 * 4. Pay and call, ONLY within an explicit ceiling (atomic USDG). The payer signs an EIP-3009 authorization
 * for exactly the quoted amount; Tollex settles it on chain and returns the result with a receipt.
 */
export async function buy(account: LocalAccount, toolId: string, input: unknown, maxAtomicUsdg: bigint) {
  const fetchWithPayment = wrapFetchWithPaymentFromConfig(fetch, {
    schemes: [{ network: NETWORK, client: new ExactEvmScheme(account) }],
    // USDG on Robinhood Chain is not one of @x402's default assets: allow it explicitly, capped per payment.
    spendControls: { allowedAssets: [{ network: NETWORK, asset: USDG, maxAmountPerPayment: maxAtomicUsdg.toString() }] },
    paymentRequirementsSelector: (_v, accepts) => {
      const ok = accepts.find((a) => a.network === NETWORK && getAddress(a.asset) === getAddress(USDG) && BigInt(a.amount) <= maxAtomicUsdg);
      if (!ok) throw new Error(`refusing to pay: no option on ${NETWORK} in USDG at or below ${maxAtomicUsdg} atomic units`);
      return ok;
    },
  });
  const r = await fetchWithPayment(`${TOLLEX}/tools/${toolId}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(input) });
  const header = r.headers.get("payment-response");
  const settlement = header ? decodePaymentResponseHeader(header) : null;
  const body = await r.json().catch(() => null);
  // 402 after paying = rejected before anything was broadcast (e.g. insufficient balance): nothing moved.
  return { status: r.status, body, settlement };
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
