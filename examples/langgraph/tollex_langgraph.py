"""Tollex as tools for a LangChain 1.x agent (runs on LangGraph).

pip install -r requirements.txt  (plus your model provider package, e.g. langchain-openai or langchain-anthropic)
TOLLEX_AGENT_MODEL="<provider:model>" python tollex_langgraph.py "What is the USDG balance of 0x2eB98e76db13287eD4AEE5F1C7f14a7e378966B7?"

The agent plans and reads prices for free. It can only pay if the operator sets TOLLEX_ALLOW_PAYMENTS=1,
TOLLEX_MAX_ATOMIC_USDG and TOLLEX_PRIVATE_KEY (see ../python/tollex_tools.py).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
from langchain.agents import create_agent  # noqa: E402
from langchain_core.tools import tool  # noqa: E402

import tollex_tools as t  # noqa: E402

TOOLS = [tool(f) for f in t.TOOLS]

SYSTEM = (
    "You can buy paid capabilities from Tollex on Robinhood Chain. Always call tollex_plan first (free), then "
    "tollex_terms to see the exact price. Only call tollex_buy when the user asked for the result and the price is "
    "acceptable. A 'rejected' result means nothing was charged. Report the Blockscout link of any payment."
)


def main() -> None:
    model = os.environ.get("TOLLEX_AGENT_MODEL")
    if not model:
        raise SystemExit("set TOLLEX_AGENT_MODEL, e.g. a LangChain model string such as 'openai:<model>'")
    agent = create_agent(model, tools=TOOLS, system_prompt=SYSTEM)
    question = " ".join(sys.argv[1:]) or "What does Tollex charge for the latest block header on Robinhood Chain?"
    for step in agent.stream({"messages": [{"role": "user", "content": question}]}, stream_mode="values"):
        step["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()
