"""Tollex tools for a CrewAI agent (CrewAI 1.15, Python 3.10-3.13).

pip install -r requirements.txt
TOLLEX_AGENT_MODEL="<provider/model>" python tollex_crewai.py "USDG balance of 0x2eB98e76db13287eD4AEE5F1C7f14a7e378966B7"

Planning and prices are free. Paying requires TOLLEX_ALLOW_PAYMENTS=1, TOLLEX_MAX_ATOMIC_USDG and
TOLLEX_PRIVATE_KEY set by the operator (see ../python/tollex_tools.py).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
from crewai import Agent, Crew, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402

import tollex_tools as t  # noqa: E402


@tool("tollex_plan")
def plan(need: str) -> str:
    """Find the Tollex capability that fits a need, with its id. Free, never spends."""
    return t.tollex_plan(need)


@tool("tollex_terms")
def terms(tool_id: str, input_json: str) -> str:
    """Exact x402 price (atomic USDG), recipient and network for calling a capability with a JSON input. Free."""
    return t.tollex_terms(tool_id, input_json)


@tool("tollex_buy")
def buy(tool_id: str, input_json: str) -> str:
    """Pay for and run a Tollex capability with real USDG on Robinhood Chain, within the operator's ceiling."""
    return t.tollex_buy(tool_id, input_json)


@tool("tollex_verify_receipt")
def verify(receipt_id: str) -> str:
    """Verify a Tollex execution receipt (content hash and signature by an active Tollex key)."""
    return t.tollex_verify_receipt(receipt_id)


TOOLS = [plan, terms, buy, verify]


def main() -> None:
    model = os.environ.get("TOLLEX_AGENT_MODEL")
    if not model:
        raise SystemExit("set TOLLEX_AGENT_MODEL to a CrewAI/LiteLLM model string")
    need = " ".join(sys.argv[1:]) or "latest block header on Robinhood Chain"
    analyst = Agent(
        role="On-chain analyst",
        goal="Answer questions about Robinhood Chain using paid Tollex capabilities, spending only within limits",
        backstory="Always plan with tollex_plan and check tollex_terms before buying. A rejected payment charged nothing.",
        tools=TOOLS,
        llm=model,
    )
    task = Task(description=f"Use Tollex to answer: {need}. Report the price and, if you paid, the Blockscout link.", expected_output="The answer, the price paid (or that nothing was paid) and any Blockscout link.", agent=analyst)
    print(Crew(agents=[analyst], tasks=[task]).kickoff())


if __name__ == "__main__":
    main()
