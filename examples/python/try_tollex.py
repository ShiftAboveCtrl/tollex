"""python try_tollex.py [--need "..."] [--pay --max 10000]

Without --pay nothing is signed or spent. With --pay, TOLLEX_PRIVATE_KEY must hold USDG on Robinhood Chain
mainnet; the call is refused locally if the price exceeds --max (atomic USDG, 6 decimals).
"""
import argparse
import json
import os

import tollex_client as tollex

p = argparse.ArgumentParser()
p.add_argument("--need", default="latest block header on Robinhood Chain")
p.add_argument("--pay", action="store_true")
p.add_argument("--max", type=int, default=0)
a = p.parse_args()
inp = {"block": "latest"}

d = tollex.discover()
print(f"1. {d['name']}: {d['capabilities']['count']} capabilities on {', '.join(d['payment']['networks'])}")
plan = tollex.plan(a.need, inp)["plan"]
tool = (plan.get("selected") or {}).get("toolId")
if not tool:
    raise SystemExit(f'no capability fits "{a.need}"')
print(f"2. plan (free): {tool} ({plan['eligible']} eligible of {plan['candidates']})")
t = tollex.terms(tool, inp)
print(f"3. terms: {t['amount']} atomic USDG ({t['amount'] / 1e6} USDG) to {t['option']['payTo']}")

if not a.pay:
    print("4. not paying (add --pay --max <atomic USDG> with TOLLEX_PRIVATE_KEY set to buy)")
    raise SystemExit(0)
try:
    r = tollex.buy(os.environ["TOLLEX_PRIVATE_KEY"], tool, inp, a.max)
except ValueError as e:
    raise SystemExit(f"4. refused locally: {e}")
except tollex.Rejected as e:
    raise SystemExit(f"4. rejected before anything was sent on chain (nothing moved): {e}")
tx = (r["settlement"] or {}).get("transaction")
print(f"4. paid: tx {tx} -> {tollex.BLOCKSCOUT}{tx}")
print(json.dumps(r["result"], indent=2)[:800])
