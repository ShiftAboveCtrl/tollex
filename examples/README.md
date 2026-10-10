# Examples

Each example runs against the live production API (`https://api.tollex.org`, Robinhood Chain mainnet) and
follows the same flow: discover, plan for free, read the exact x402 price, pay only with an explicit
ceiling, verify the receipt. **Nothing pays unless you pass `--pay` (or set `TOLLEX_ALLOW_PAYMENTS=1`) with a
key that holds USDC on Base (default rail, `--rail base`) or USDG on Robinhood Chain (`--rail robinhood`).**

**One command, nothing to clone:** `TOLLEX_PRIVATE_KEY=0x... uv run https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/examples/agent-check/agent_check.py --pay --max 10000` ([agent-check/](agent-check/agent_check.py); `--tool <id> --input '<json>'` buys a capability the same way).

**Make your first real payment:** `npm run first-payment -- --pay --max 10000` (TypeScript) or
`python first_payment.py --pay --max 10000` (Python) buys `GET /v1/agent-check`, about 0.008 USD.

| Example | Run | Verified |
| --- | --- | --- |
| [curl](curl/try-tollex.sh) | `examples/curl/try-tollex.sh` | discovery, plan, 402 terms, receipt, A2A |
| [TypeScript](typescript/) | `npm install && npm run try` | `@x402/fetch` 2.28 payment path; receipt verification |
| [Python](python/) | `pip install -r requirements.txt && python try_tollex.py` | EIP-3009 signing; receipt verification |
| [A2A](a2a/a2a_tollex.py) | `python a2a/a2a_tollex.py` | JSON-RPC 1.0 + a2a-x402 payment flow |
| [LangChain / LangGraph](langgraph/tollex_langgraph.py) | `TOLLEX_AGENT_MODEL=... python tollex_langgraph.py "..."` | tools + `create_agent` (LangChain 1.4) |
| [CrewAI](crewai/tollex_crewai.py) | `TOLLEX_AGENT_MODEL=... python tollex_crewai.py "..."` | tools + Crew (CrewAI 1.15, Python 3.10 to 3.13) |
| [Agent demo](agent-demo/agent_demo.py) | `python agent-demo/agent_demo.py "<need>"` | full loop with a human approval prompt and receipt check |
| [Google ADK](google-adk/tollex_agent/agent.py) | `adk run tollex_agent` (from `google-adk/`) | function tools (google-adk 2.11) |

"Verified" means the example was run against production on 2026-10-09: free paths end to end, and the payment
path with an empty throwaway wallet, which production correctly rejected as `insufficient_balance`
(signature and terms accepted; nothing moved).

The framework examples share [python/tollex_tools.py](python/tollex_tools.py): `tollex_plan`, `tollex_terms`,
`tollex_buy` (operator opt-in and ceiling from the environment, never from the model) and
`tollex_verify_receipt`.
