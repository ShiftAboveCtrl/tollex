"""An autonomous-style agent loop against Tollex production, with a human approval step.

    python agent_demo.py "USDG balance of 0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168"

discover -> plan (free) -> terms (402) -> local ceiling -> ask the human -> pay -> result -> verify receipt.
Nothing is signed unless TOLLEX_PRIVATE_KEY is set AND the human approves (or TOLLEX_AUTO_APPROVE_MAX, in atomic
USDG, covers the price). TOLLEX_MAX_ATOMIC_USDG is the hard ceiling (default 10000 = 0.01 USDG).
Dependencies: pip install -r ../python/requirements.txt
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import tollex_client as tollex  # noqa: E402

need = " ".join(sys.argv[1:]) or "latest block on Robinhood Chain"
ceiling = int(os.environ.get("TOLLEX_MAX_ATOMIC_USDG", "10000"))
auto = int(os.environ.get("TOLLEX_AUTO_APPROVE_MAX", "0"))
key = os.environ.get("TOLLEX_PRIVATE_KEY")


def step(n, text):
    print(f"[{n}] {text}")


d = tollex.discover()
step(1, f"discovered {d['name']}: {d['capabilities']['count']} capabilities, payment on {d['payment']['networks'][0]} in {d['payment']['assets'][0]['symbol']}")

# The agent fills the input from the need where it can; a real agent would use its model for this.
addr = re.search(r"0x[0-9a-fA-F]{40}", need)
guess = {"address": addr.group(0)} if addr else {"block": "latest"}
plan = tollex.plan(need, guess, ceiling)["plan"]
sel = plan.get("selected")
if not sel:
    sys.exit(f"[2] no capability fits '{need}' within {ceiling} atomic USDG ({plan.get('eligible', 0)} eligible); nothing spent")
tool = sel["toolId"]
step(2, f"plan (free): {tool}, {plan['eligible']} eligible of {plan['candidates']}")

t = tollex.terms(tool, guess)
step(3, f"terms: {t['amount']} atomic USDG ({t['amount'] / 1e6} USDG) to {t['option']['payTo']} on {t['option']['network']}")

if t["amount"] > ceiling:
    sys.exit(f"[4] refused locally: price {t['amount']} > ceiling {ceiling}; nothing signed")
step(4, f"within the ceiling ({ceiling})")

if not key:
    sys.exit("[5] stopping before payment: set TOLLEX_PRIVATE_KEY (a wallet holding USDG on Robinhood Chain) to continue")
if t["amount"] <= auto:
    step(5, f"auto-approved by TOLLEX_AUTO_APPROVE_MAX={auto}")
else:
    answer = input(f"[5] Pay {t['amount'] / 1e6} USDG for {tool}? [y/N] ").strip().lower()
    if answer != "y":
        sys.exit("[5] declined by the human; nothing signed")

try:
    r = tollex.buy(key, tool, guess, ceiling)
except tollex.Rejected as e:
    sys.exit(f"[6] rejected before anything was sent on chain, nothing moved: {e}"
             + ("\n    fund the payer with USDG on Robinhood Chain" if "balance" in str(e) else ""))
except RuntimeError as e:
    sys.exit(f"[6] not charged: {e}")
s = r["settlement"] or {}
tx = s.get("transaction")
step(6, f"paid: {tollex.BLOCKSCOUT}{tx}" if tx else f"status {r['status']}: poll the operation before retrying")
print(json.dumps(r["result"], indent=2)[:600])

receipt = (s.get("extensions") or {}).get("tollex-receipt", {}).get("info")
if receipt:
    v = tollex.verify_receipt(receipt)
    step(7, f"receipt {receipt['body']['receiptId']}: valid={v['valid']} (hash {v['contentHashMatches']}, active signer {v['signerIsActiveTollexKey']})")
else:
    step(7, "no receipt in the settlement response; fetch it later from the operation")
