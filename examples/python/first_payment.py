"""Make your first real Tollex payment: GET /v1/agent-check (the cheapest paid call, about 0.008 USD).

    python first_payment.py                                         # show the price on each rail
    TOLLEX_PRIVATE_KEY=0x... python first_payment.py --pay --max 10000 [--rail base|robinhood]

--rail base (default): USDC on Base. --rail robinhood: USDG on Robinhood Chain. --max: per-call ceiling in
atomic units (6 decimals). Nothing is signed without --pay.
"""
import argparse
import json
import os

import tollex_client as tollex

p = argparse.ArgumentParser()
p.add_argument("--rail", default="base", choices=sorted(tollex.RAILS))
p.add_argument("--pay", action="store_true")
p.add_argument("--max", type=int, default=0)
a = p.parse_args()

for name in tollex.RAILS:
    try:
        t = tollex.terms_for("GET", "/v1/agent-check", None, name)
        print(f"{name}: {t['amount']} atomic {tollex.RAILS[name]['symbol']} ({t['amount'] / 1e6}) to {t['option']['payTo']} on {tollex.RAILS[name]['network']}")
    except RuntimeError as e:
        print(f"{name}: {e}")
if not a.pay:
    raise SystemExit("not paying (add --pay --max <atomic units> and set TOLLEX_PRIVATE_KEY)")
t = tollex.terms_for("GET", "/v1/agent-check", None, a.rail)
try:
    r = tollex.pay(os.environ["TOLLEX_PRIVATE_KEY"], t, tollex.SpendPolicy(a.max, a.max, [a.rail]))
except ValueError as e:
    raise SystemExit(f"refused locally: {e}")
except tollex.Rejected as e:
    raise SystemExit(f"rejected before anything was sent on chain (nothing moved): {e}")
print(f"paid on {tollex.RAILS[a.rail]['network']}: {r['explorer']}")
print(json.dumps(r["result"], indent=2))
receipt = ((r["settlement"] or {}).get("extensions") or {}).get("tollex-receipt", {}).get("info")
if receipt:
    print("receipt", receipt["body"]["receiptId"], tollex.verify_receipt(receipt))
