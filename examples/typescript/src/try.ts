/**
 * npm run try -- [--need "..."] [--pay --max 10000]
 * Without --pay nothing is signed or spent. With --pay, TOLLEX_PRIVATE_KEY must hold USDG on Robinhood
 * Chain mainnet; the call is refused locally if the price exceeds --max (atomic USDG, 6 decimals).
 */
import { privateKeyToAccount } from "viem/accounts";
import { buy, discover, plan, terms } from "./tollex.js";

const arg = (k: string) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : undefined);
const need = arg("--need") ?? "latest block header on Robinhood Chain";
const input = { block: "latest" };

const d = await discover();
console.log(`1. ${d.name}: ${d.capabilities.count} capabilities on ${d.payment.networks.join(", ")} in ${d.payment.assets.map((a) => a.symbol).join(", ")}`);
const p = await plan(need, input);
const toolId = p.plan.selected?.toolId;
if (!toolId) throw new Error(`no capability fits "${need}"`);
console.log(`2. plan (free): "${need}" -> ${toolId} (${p.plan.eligible} eligible of ${p.plan.candidates})`);
const t = await terms(toolId, input);
console.log(`3. terms: ${t.amount} atomic USDG (${Number(t.amount) / 1e6} USDG) to ${t.payTo} on Robinhood Chain`);

if (!process.argv.includes("--pay")) {
  console.log("4. not paying (add --pay --max <atomic USDG> with TOLLEX_PRIVATE_KEY set to buy)");
  process.exit(0);
}
const max = BigInt(arg("--max") ?? "0");
const key = process.env.TOLLEX_PRIVATE_KEY as `0x${string}` | undefined;
if (!key) throw new Error("TOLLEX_PRIVATE_KEY is required to pay");
const r = await buy(privateKeyToAccount(key), toolId, input, max).catch((e: Error) => {
  console.log(`4. refused locally, nothing signed: ${e.message.replace(/^Failed to create payment payload: /, "")}`);
  process.exit(2);
  return null as never;
});
if (r.status === 200) {
  console.log(`4. paid: tx ${r.settlement?.transaction} -> https://robinhoodchain.blockscout.com/tx/${r.settlement?.transaction}`);
  console.log(JSON.stringify(r.body, null, 2).slice(0, 800));
} else {
  // A 402 here means the payment was refused before anything was sent on chain (nothing moved).
  console.log(`4. not settled (HTTP ${r.status}): ${JSON.stringify(r.body).slice(0, 300)}`);
}
