/**
 * npm run try -- [--need "..."] [--rail base|robinhood] [--pay --max 10000]
 * Without --pay nothing is signed or spent. With --pay, TOLLEX_PRIVATE_KEY must hold USDC on Base (default
 * rail) or USDG on Robinhood Chain (--rail robinhood); the call is refused locally if the price exceeds
 * --max (atomic units, 6 decimals).
 */
import { privateKeyToAccount } from "viem/accounts";
import { SpendPolicy, buy, discover, plan, rail, terms, type RailName } from "./tollex.js";

const arg = (k: string) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : undefined);
const need = arg("--need") ?? "latest block header on Robinhood Chain";
const input = { block: "latest" };
const railName = (arg("--rail") ?? "base") as RailName;
const r = rail(railName);

const d = await discover();
console.log(`1. ${d.name}: ${d.capabilities.count} capabilities on ${d.payment.networks.join(", ")} in ${d.payment.assets.map((a) => a.symbol).join(", ")}`);
const p = await plan(need, input);
const toolId = p.plan.selected?.toolId;
if (!toolId) throw new Error(`no capability fits "${need}"`);
console.log(`2. plan (free): "${need}" -> ${toolId} (${p.plan.eligible} eligible of ${p.plan.candidates})`);
const init = { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(input) };
const t = await terms(`/tools/${toolId}`, init, r);
console.log(`3. terms: ${t.amount} atomic ${r.symbol} (${Number(t.amount) / 1e6}) to ${t.payTo} on ${r.network}`);

if (!process.argv.includes("--pay")) {
  console.log("4. not paying (add --pay --max <atomic units> with TOLLEX_PRIVATE_KEY set to buy)");
  process.exit(0);
}
const max = BigInt(arg("--max") ?? "0");
const key = process.env.TOLLEX_PRIVATE_KEY as `0x${string}` | undefined;
if (!key) throw new Error("TOLLEX_PRIVATE_KEY is required to pay");
const res = await buy(privateKeyToAccount(key), `/tools/${toolId}`, init, r, new SpendPolicy(max, max, [railName])).catch((e: Error) => {
  console.log(`4. refused locally, nothing signed: ${e.message.replace(/^Failed to create payment payload: /, "")}`);
  process.exit(2);
  return null as never;
});
if (res.status === 200) {
  console.log(`4. paid: ${res.explorer}`);
  console.log(JSON.stringify(res.body, null, 2).slice(0, 800));
} else {
  // A 402 here means the payment was refused before anything was sent on chain (nothing moved).
  console.log(`4. not settled (HTTP ${res.status}): ${JSON.stringify(res.body).slice(0, 300)}`);
}
