"""python try_tollex.py [--need "..."] [--rail base|robinhood] [--pay --max 10000]

Without --pay nothing is signed or spent. With --pay, TOLLEX_PRIVATE_KEY must hold USDC on Base (default
rail) or USDG on Robinhood Chain (--rail robinhood); the call is refused locally above --max (atomic, 6 decimals).
"""
import argparse
import json
import os

import tollex_client as tollex

p = argparse.ArgumentParser()
p.add_argument("--need", default="latest block header on Robinhood Chain")
p.add_argument("--pay", action="store_true")
p.add_argument("--max", type=int, default=0)
p.add_argument("--rail", default="base", choices=sorted(tollex.RAILS))
a = p.parse_args()
inp = {"block": "latest"}

d = tollex.discover()
print(f"1. {d['name']}: {d['capabilities']['count']} capabilities on {', '.join(d['payment']['networks'])}")
plan = tollex.plan(a.need, inp)["plan"]
tool = (plan.get("selected") or {}).get("toolId")
if not tool:
    raise SystemExit(f'no capability fits "{a.need}"')
print(f"2. plan (free): {tool} ({plan['eligible']} eligible of {plan['candidates']})")
t = tollex.terms(tool, inp, a.rail)
print(f"3. terms: {t['amount']} atomic {tollex.RAILS[a.rail]['symbol']} ({t['amount'] / 1e6}) to {t['option']['payTo']} on {tollex.RAILS[a.rail]['network']}")

if not a.pay:
    print("4. not paying (add --pay --max <atomic units> [--rail base|robinhood] with TOLLEX_PRIVATE_KEY set to buy)")
    raise SystemExit(0)
try:
    r = tollex.pay(os.environ["TOLLEX_PRIVATE_KEY"], t, tollex.SpendPolicy(a.max, a.max, [a.rail]))
except ValueError as e:
    raise SystemExit(f"4. refused locally: {e}")
except tollex.Rejected as e:
    raise SystemExit(f"4. rejected before anything was sent on chain (nothing moved): {e}")
tx = (r["settlement"] or {}).get("transaction")
print(f"4. paid: {r['explorer']}")
print(json.dumps(r["result"], indent=2)[:800])
