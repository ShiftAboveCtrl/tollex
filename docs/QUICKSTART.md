# Quickstart

## 60 seconds: see it work (no wallet, nothing spent)

```bash
git clone https://github.com/ShiftAboveCtrl/tollex.git && cd tollex
examples/curl/try-tollex.sh
```

You will see the service descriptor, a free plan for a need, the exact x402 payment terms for one call,
a real receipt from the first mainnet settlement, and an A2A planning task.

## Try a real mainnet call (one command)

```bash
TOLLEX_PRIVATE_KEY=0x... uv run https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/examples/agent-check/agent_check.py --pay --max 10000
```

Details and five capabilities worth a first call: [TRY.md](TRY.md).

## Try Tollex now: your first real payment

One paid call, about 0.008 USD, priced the same on both rails: `GET https://api.tollex.org/v1/agent-check`. It
returns which rail you paid on, the live state of every rail and the chain heads, with a signed receipt.
Tollex never holds your key or funds: you sign one exact, single-use authorization per call, never above
the ceiling you pass.

**Option A: I already have USDC on Base** (the default x402 asset; nothing else to configure)

```bash
cd examples/typescript && npm install
npm run first-payment                                                   # prices on each rail, nothing signed
TOLLEX_PRIVATE_KEY=0x... npm run first-payment -- --pay --max 10000      # pay at most 0.01 USDC on Base
```

```bash
cd examples/python && pip install -r requirements.txt
TOLLEX_PRIVATE_KEY=0x... python first_payment.py --pay --max 10000
```

**Option B: I have USDG on Robinhood Chain**

```bash
TOLLEX_PRIVATE_KEY=0x... npm run first-payment -- --pay --max 10000 --rail robinhood
TOLLEX_PRIVATE_KEY=0x... python first_payment.py --pay --max 10000 --rail robinhood
```

Any standard x402 client works too: request the URL, read the `402`, pay the option for the rail you hold. With
`@x402/fetch` and Base USDC that is just a wallet and a cap; for USDG add `spendControls.allowedAssets`.

## 5 minutes: from discovery to a capability purchase

Plan for free, read the price, buy a capability, verify the receipt (`--rail base` is the default):

```bash
cd examples/typescript
npm run try                                                       # discover, plan, show the price: nothing signed
TOLLEX_PRIVATE_KEY=0x... npm run try -- --pay --max 10000          # USDC on Base
TOLLEX_PRIVATE_KEY=0x... npm run try -- --pay --max 10000 --rail robinhood
npm run verify-receipt -- rcpt_i-xD2HIyq46pjn0z
```

```bash
cd examples/python
python try_tollex.py
TOLLEX_PRIVATE_KEY=0x... python try_tollex.py --pay --max 10000 [--rail robinhood]
python verify_receipt.py rcpt_i-xD2HIyq46pjn0z
```

A2A (JSON-RPC 1.0 + the a2a-x402 extension; the example sends `constraints.networks` for the chosen rail):

```bash
python examples/a2a/a2a_tollex.py                                 # plan, then show the payment-required task
TOLLEX_PRIVATE_KEY=0x... python examples/a2a/a2a_tollex.py --pay --max 10000 [--rail robinhood]
```

Agent with a human approval prompt and a session budget: [examples/agent-demo](../examples/agent-demo/agent_demo.py).

Agent frameworks (the agent plans and reads prices freely; it can only pay when you set
`TOLLEX_ALLOW_PAYMENTS=1`, a hard `TOLLEX_MAX_ATOMIC_USDG`, optionally `TOLLEX_MAX_SESSION_ATOMIC` and `TOLLEX_RAIL`,
and `TOLLEX_PRIVATE_KEY`; the model can change none of them):

| Framework | File |
| --- | --- |
| LangChain 1.x / LangGraph | [examples/langgraph/tollex_langgraph.py](../examples/langgraph/tollex_langgraph.py) |
| CrewAI | [examples/crewai/tollex_crewai.py](../examples/crewai/tollex_crewai.py) |
| Google ADK | [examples/google-adk/tollex_agent/agent.py](../examples/google-adk/tollex_agent/agent.py) |

## Give this prompt to your coding agent

Short version (ChatGPT, Codex, Claude Code, Gemini, Cursor):

```text
Integrate this project with Tollex. Read https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/AGENTS.md
and use only its public production interfaces at https://api.tollex.org. Never spend funds without my explicit
approval and a ceiling I set. Discover the capabilities, then build the minimum working integration.
```

Detailed version:

```
Integrate Tollex (https://api.tollex.org) into this project. Read
https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/AGENTS.md first and follow it exactly.
Use the service descriptor and OpenAPI rather than guessing. Add a free "plan" step with POST /v1/resolve,
show the live x402 price before any payment, and only pay when I approve, never above a ceiling I set in
configuration (not in prompts). Accept only network eip155:4663 and USDG. Verify every receipt against
/.well-known/tollex-receipt-keys and show the Blockscout link of each payment.
```

## Pricing

Every capability has one price per call, the same in USDC on Base and in USDG on Robinhood Chain (both 6-decimal
USD stablecoins). A price is at least the cost of settling a payment on Robinhood Chain plus a margin, so it moves
with network gas (about 7,800 to 7,900 atomic, 0.0079 USD, in October 2026). If a rail's own settlement cost rises
above the price, that rail is left out of new `402`s until it falls again; the other rail keeps serving. The `402`
terms of each call are authoritative and never change after you sign. Planning, quotes, catalogue, receipts and
operation status are free.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `@x402/fetch`: "rejected by spendControls ... allowedAssets" | you chose USDG; it is not an `@x402` default asset | pass `spendControls.allowedAssets` with network `eip155:4663`, the USDG address and a `maxAmountPerPayment`, or pay with USDC on Base |
| `402 invalid_exact_evm_insufficient_balance` | the payer holds too little of the chosen asset on that chain | fund it, or pay on the other rail; nothing was charged |
| `402 invalid_exact_evm_*` (signature, value, recipient) | signed terms differ from the live terms | re-read the `402`; sign exactly `amount` to `payTo` with the rail's chain id (8453 Base, 4663 Robinhood Chain) |
| `409 quote_mismatch` "priced on ..." | the quote was priced on the other rail | request the quote with `"network"` (or resolve with `constraints.networks`) for the rail you pay on |
| only one rail in the `402` | the other rail's settlement cost is above the price right now, or your request carries a quote for one rail | pay on the offered rail or retry later |
| `503 paid_calls_paused` | no rail can settle at this price right now | retry after `Retry-After`; nothing charged |
| no payment option | your client offers another network or asset | Tollex accepts USDC on `eip155:8453` and USDG on `eip155:4663` only |
| lost response | network failure after sending | `GET /tollex/operations/{operationId}`; do not re-sign |

## Live state

- [Activity](https://tollex.org/activity/): settled operations (with Blockscout links) and rejected attempts.
- [Live Production Verification](../.github/workflows/verify-live.yml): public checks twice a day.
