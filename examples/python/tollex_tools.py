"""Framework-agnostic Tollex tools for agents (plain functions with docstrings and type hints).

Paying is OFF unless the operator opts in:
  TOLLEX_ALLOW_PAYMENTS=1            enable tollex_buy
  TOLLEX_MAX_ATOMIC_USDG=10000       hard per-call ceiling in atomic units (6 decimals); required
  TOLLEX_MAX_SESSION_ATOMIC=50000    budget for this process (default: 5 x the per-call ceiling)
  TOLLEX_RAIL=base                   rail to pay on: base (USDC on Base) or robinhood (USDG on Robinhood Chain)
  TOLLEX_PRIVATE_KEY=0x...           payer key holding that asset (keep it out of prompts)
The model can never raise the ceiling, the budget or change the rail: they come from the environment,
not from tool arguments.
"""
from __future__ import annotations

import json
import os

import tollex_client as tollex


def tollex_plan(need: str, max_cost_atomic_usdg: int | None = None) -> str:
    """Find the Tollex capability that fits a need, with its price. Free, never spends.

    Args:
        need: what the agent needs, e.g. "USDG balance of 0xabc..." or "latest block on Robinhood Chain".
        max_cost_atomic_usdg: optional price ceiling in atomic USDG (6 decimals).
    """
    p = tollex.plan(need, None, max_cost_atomic_usdg)["plan"]
    sel = p.get("selected")
    if not sel:
        return json.dumps({"selected": None, "eligible": p.get("eligible", 0)})
    return json.dumps({"toolId": sel["toolId"], "eligible": p["eligible"], "candidates": p["candidates"]})


RAIL = os.environ.get("TOLLEX_RAIL", "base")
_policy: "tollex.SpendPolicy | None" = None


def _spend_policy() -> "tollex.SpendPolicy":
    global _policy
    if _policy is None:
        per_call = int(os.environ["TOLLEX_MAX_ATOMIC_USDG"])
        _policy = tollex.SpendPolicy(per_call, int(os.environ.get("TOLLEX_MAX_SESSION_ATOMIC", per_call * 5)), [RAIL])
    return _policy


def tollex_terms(tool_id: str, input_json: str) -> str:
    """Get the exact x402 payment terms (price in atomic USDG, recipient, network) for a capability call. Free.

    Args:
        tool_id: capability id from tollex_plan, e.g. "wallet_token_balance".
        input_json: the capability input as a JSON object string, e.g. '{"address": "0x..."}'.
    """
    t = tollex.terms(tool_id, json.loads(input_json), RAIL)
    return json.dumps({"toolId": tool_id, "amountAtomic": t["amount"], "usd": t["amount"] / 1e6, "asset": tollex.RAILS[RAIL]["symbol"], "payTo": t["option"]["payTo"], "network": tollex.RAILS[RAIL]["network"]})


def tollex_buy(tool_id: str, input_json: str) -> str:
    """Pay for and run a Tollex capability (real money on the operator's rail), within the operator's ceiling and budget.

    Args:
        tool_id: capability id from tollex_plan.
        input_json: the capability input as a JSON object string.
    """
    if os.environ.get("TOLLEX_ALLOW_PAYMENTS") != "1":
        return json.dumps({"error": "payments disabled: the operator must set TOLLEX_ALLOW_PAYMENTS=1 and TOLLEX_MAX_ATOMIC_USDG"})
    try:
        r = tollex.pay(os.environ["TOLLEX_PRIVATE_KEY"], tollex.terms(tool_id, json.loads(input_json), RAIL), _spend_policy())
    except ValueError as e:
        return json.dumps({"error": "over_ceiling", "detail": str(e), "charged": False})
    except tollex.Rejected as e:
        return json.dumps({"error": "rejected", "reason": str(e), "charged": False, "note": "refused before anything was sent on chain"})
    tx = (r["settlement"] or {}).get("transaction")
    receipt = ((r["settlement"] or {}).get("extensions") or {}).get("tollex-receipt", {}).get("info")
    return json.dumps({"result": r["result"], "transaction": tx, "blockscout": r["explorer"], "receipt": receipt})[:6000]


def tollex_verify_receipt(receipt_id: str) -> str:
    """Verify a Tollex execution receipt: canonical content hash and signature by an active Tollex key.

    Args:
        receipt_id: e.g. "rcpt_i-xD2HIyq46pjn0z".
    """
    return json.dumps(tollex.verify_receipt(tollex.get_receipt(receipt_id)))


TOOLS = [tollex_plan, tollex_terms, tollex_buy, tollex_verify_receipt]
