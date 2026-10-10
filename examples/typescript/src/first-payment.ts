/**
 * Make your first real Tollex payment: GET /v1/agent-check (the cheapest paid call, about 0.008 USD).
 *
 *   npm run first-payment                                   # show the price on each rail, sign nothing
 *   TOLLEX_PRIVATE_KEY=0x... npm run first-payment -- --pay --max 10000 [--rail base|robinhood]
 *
 * --rail base (default) pays USDC on Base; --rail robinhood pays USDG on Robinhood Chain. --max is the
 * per-call ceiling in atomic units (6 decimals; 10000 = 0.01 USD). The answer tells you which rail you paid
 * on, the live state of every rail and the chain heads; the receipt in PAYMENT-RESPONSE is verified here.
 */
import { privateKeyToAccount } from "viem/accounts";
import { RAILS, SpendPolicy, buy, rail, terms, verifyReceipt, type RailName, type SignedReceipt } from "./tollex.js";

const arg = (k: string) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : undefined);
const railName = (arg("--rail") ?? "base") as RailName;
const r = rail(railName);
for (const [name, x] of Object.entries(RAILS)) {
  const t = await terms("/v1/agent-check", {}, x).catch((e: Error) => ({ error: e.message }));
  console.log("error" in t ? `${name}: ${t.error}` : `${name}: ${t.amount} atomic ${x.symbol} (${Number(t.amount) / 1e6}) to ${t.payTo} on ${x.network}`);
}
if (!process.argv.includes("--pay")) {
  console.log("not paying (add --pay --max <atomic units> and set TOLLEX_PRIVATE_KEY)");
  process.exit(0);
}
const max = BigInt(arg("--max") ?? "0");
const key = process.env.TOLLEX_PRIVATE_KEY as `0x${string}` | undefined;
if (!key) throw new Error("TOLLEX_PRIVATE_KEY is required to pay");
const policy = new SpendPolicy(max, max, [railName]);
const res = await buy(privateKeyToAccount(key), "/v1/agent-check", {}, r, policy).catch((e: Error) => {
  console.log(`refused locally, nothing signed: ${e.message.replace(/^Failed to create payment payload: /, "")}`);
  process.exit(2);
  return null as never;
});
if (res.status !== 200) {
  console.log(`not settled (HTTP ${res.status}, nothing moved): ${JSON.stringify(res.body).slice(0, 300)}`);
  process.exit(1);
}
console.log(`paid on ${r.network}: ${res.explorer}`);
console.log(JSON.stringify(res.body, null, 2));
const receipt = (res.settlement as { extensions?: Record<string, { info?: SignedReceipt }> } | null)?.extensions?.["tollex-receipt"]?.info;
if (receipt) console.log(`receipt ${receipt.body.receiptId}:`, await verifyReceipt(receipt));
