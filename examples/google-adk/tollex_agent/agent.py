"""Tollex tools for a Google ADK agent.

pip install -r requirements.txt
adk run tollex_agent        (or: adk web)    with your model credentials configured for ADK

Planning and prices are free. Paying requires TOLLEX_ALLOW_PAYMENTS=1, TOLLEX_MAX_ATOMIC_USDG and
TOLLEX_PRIVATE_KEY set by the operator (see ../../python/tollex_tools.py).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python"))
from google.adk.agents import Agent  # noqa: E402

from tollex_tools import tollex_buy, tollex_plan, tollex_terms, tollex_verify_receipt  # noqa: E402

root_agent = Agent(
    name="tollex_agent",
    model=os.environ.get("TOLLEX_AGENT_MODEL", "gemini-2.5-flash"),
    description="Buys paid capabilities from Tollex on Robinhood Chain (x402, USDG) and verifies the receipts.",
    instruction=(
        "Always call tollex_plan first (free), then tollex_terms for the exact price. Call tollex_buy only when the "
        "user wants the result and the price is acceptable; a 'rejected' result means nothing was charged. Report the "
        "Blockscout link of every payment and offer to verify its receipt with tollex_verify_receipt."
    ),
    tools=[tollex_plan, tollex_terms, tollex_buy, tollex_verify_receipt],
)
