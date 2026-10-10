"""Tollex over A2A (JSON-RPC 1.0) with the a2a-x402 payment extension.

python a2a_tollex.py                       plan only (free), then show the payment-required task
python a2a_tollex.py --pay --max 10000 [--rail base|robinhood]   pay with TOLLEX_PRIVATE_KEY (USDC on Base by default, or USDG on Robinhood Chain), never above --max
"""
import argparse
import json
import os
import sys
import uuid

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import tollex_client as tollex  # noqa: E402  (signing helper shared with the Python example)

CARD = requests.get(f"{tollex.TOLLEX}/.well-known/agent-card.json", timeout=30).json()
ENDPOINT = CARD["supportedInterfaces"][0]["url"]  # discovered, not hard-coded


def send(data: dict, metadata: dict | None = None) -> dict:
    msg = {"role": "ROLE_USER", "messageId": str(uuid.uuid4()), "parts": [{"data": data}]}
    if metadata:
        msg["metadata"] = metadata
    r = requests.post(ENDPOINT, json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": {"message": msg}}, headers={"a2a-version": "1.0"}, timeout=120)
    j = r.json()
    if "error" in j:
        raise RuntimeError(j["error"])
    return j["result"]["task"]


p = argparse.ArgumentParser()
p.add_argument("--need", default="latest block header on Robinhood Chain")
p.add_argument("--pay", action="store_true")
p.add_argument("--rail", default="base", choices=sorted(tollex.RAILS), help="base: USDC on Base; robinhood: USDG on Robinhood Chain")
p.add_argument("--max", type=int, default=0)
a = p.parse_args()
inp = {"block": "latest"}
print(f"agent: {CARD['name']} ({len(CARD['skills'])} skills) at {ENDPOINT}")

# 1. Plan (free)
plan = send({"skill": "tollex.resolve_intent", "need": a.need, "input": inp})
print("1. resolve_intent:", plan["status"]["state"])

# 2. Execute: the first reply is a payment-required task naming the capability and the exact terms
# The network constraint makes the quote (and therefore the offered payment option) use the chosen rail.
rail = tollex.RAILS[a.rail]
task = send({"skill": "tollex.execute_intent", "need": a.need, "input": inp, "constraints": {"maxCost": str(a.max or 20000), "networks": [rail["network"]]}})
meta = task.get("metadata", {})
required = meta.get("x402.payment.required")
if task["status"]["state"] != "TASK_STATE_INPUT_REQUIRED" or not required:
    raise SystemExit(f"unexpected task: {json.dumps(task)[:300]}")
option = next((o for o in required["accepts"] if o["network"] == rail["network"] and o["asset"].lower() == rail["asset"].lower()), None)
if not option:
    raise SystemExit(f"2. no {rail['symbol']} option on {rail['network']} offered: {[o['network'] for o in required['accepts']]}")
print(f"2. payment required: {meta['tollex.toolId']} for {option['amount']} atomic {rail['symbol']} to {option['payTo']} on {rail['network']}")
if not a.pay:
    raise SystemExit("3. not paying (add --pay --max <atomic units> with TOLLEX_PRIVATE_KEY set)")
if int(option["amount"]) > a.max:
    raise SystemExit(f"3. refused locally: {option['amount']} > ceiling {a.max} (nothing signed)")

# 3. Re-send the same request with a signed x402 payment payload (EIP-3009, exactly the quoted amount)
from eth_account import Account  # noqa: E402

payload = {"x402Version": 2, "accepted": option, "resource": required["resource"], "payload": tollex._authorization(Account.from_key(os.environ["TOLLEX_PRIVATE_KEY"]), option, rail["chain_id"])}
done = send({"skill": "tollex.execute_intent", "need": a.need, "input": inp}, {"x402.payment.payload": payload, "tollex.quoteId": meta.get("tollex.quoteId")})
m = done.get("metadata", {})
status = m.get("x402.payment.status")
reason = "".join(pt.get("text", "") for pt in (done["status"].get("message") or {}).get("parts", []))
if status == "payment-rejected":
    # Refused before anything was sent on chain: nothing moved. Fix the cause (e.g. fund the wallet) and retry.
    raise SystemExit(f"3. rejected, nothing moved: {reason}")
print("3.", done["status"]["state"], status)
for r in m.get("x402.payment.receipts", []) or []:
    tx = r.get("transaction") if isinstance(r, dict) else None
    if tx:
        print(f"   settled: {rail['explorer']}{tx}")
