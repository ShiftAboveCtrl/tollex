# Quickstart

## 60 seconds: see it work (no wallet, nothing spent)

```bash
git clone https://github.com/ShiftAboveCtrl/tollex.git && cd tollex
examples/curl/try-tollex.sh
```

You will see the service descriptor, a free plan for a need, the exact x402 payment terms for one call,
a real receipt from the first mainnet settlement, and an A2A planning task.

## 5 minutes: from discovery to a verified purchase

**You need:** Node 20+ or Python 3.10+; for paying, a wallet holding a little **USDG on Robinhood Chain
mainnet** (one call costs about 0.008 USDG; the live `402` is authoritative). Tollex never holds your key
or your funds: you sign one exact, single-use authorization per call.

TypeScript (official `@x402` packages):

```bash
cd examples/typescript && npm install
npm run try                                   # discover, plan, show the price: nothing signed
TOLLEX_PRIVATE_KEY=0x... npm run try -- --pay --max 10000   # pay at most 10000 atomic USDG (0.01)
npm run verify-receipt -- rcpt_i-xD2HIyq46pjn0z
```

Python (`requests`, `eth-account`, `rfc8785`):

```bash
cd examples/python && pip install -r requirements.txt
python try_tollex.py
TOLLEX_PRIVATE_KEY=0x... python try_tollex.py --pay --max 10000
python verify_receipt.py rcpt_i-xD2HIyq46pjn0z
```

A2A (JSON-RPC 1.0 + the a2a-x402 extension):

```bash
python examples/a2a/a2a_tollex.py                    # plan, then show the payment-required task
TOLLEX_PRIVATE_KEY=0x... python examples/a2a/a2a_tollex.py --pay --max 10000
```

Agent frameworks (the agent plans and reads prices freely; it can only pay when you set
`TOLLEX_ALLOW_PAYMENTS=1`, a hard `TOLLEX_MAX_ATOMIC_USDG` and `TOLLEX_PRIVATE_KEY`):

| Framework | File |
| --- | --- |
| LangChain 1.x / LangGraph | [examples/langgraph/tollex_langgraph.py](../examples/langgraph/tollex_langgraph.py) |
| CrewAI | [examples/crewai/tollex_crewai.py](../examples/crewai/tollex_crewai.py) |
| Google ADK | [examples/google-adk/tollex_agent/agent.py](../examples/google-adk/tollex_agent/agent.py) |

## Give this prompt to your coding agent

```
Integrate Tollex (https://api.tollex.org) into this project. Read
https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/AGENTS.md first and follow it exactly.
Use the service descriptor and OpenAPI rather than guessing. Add a free "plan" step with POST /v1/resolve,
show the live x402 price before any payment, and only pay when I approve, never above a ceiling I set in
configuration (not in prompts). Accept only network eip155:4663 and USDG. Verify every receipt against
/.well-known/tollex-receipt-keys and show the Blockscout link of each payment.
```

## Pricing

Every capability is priced per call in USDG. A price is at least the cost of settling the payment on chain
plus a margin, so it moves with network gas (7800 atomic, 0.0078 USDG, on 2026-10-09). The `402` terms of
each call are authoritative and never change after you sign. Planning, quotes, catalogue, receipts and
operation status are free.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `@x402/fetch`: "rejected by spendControls ... allowedAssets" | USDG on Robinhood Chain is not an `@x402` default asset | pass `spendControls.allowedAssets` with network `eip155:4663`, the USDG address and a `maxAmountPerPayment` |
| `402 invalid_exact_evm_insufficient_balance` | the payer holds too little USDG on Robinhood Chain | fund it; nothing was charged |
| `402 invalid_exact_evm_*` (signature, value, recipient) | signed terms differ from the live terms | re-read the `402` and sign exactly `amount` to `payTo` with chain id 4663 |
| `503 paid_calls_paused` | gas spike; Tollex will not settle at a loss | retry after `Retry-After`; nothing charged |
| no payment option | your client offers another network or asset | Tollex accepts only `eip155:4663` + USDG |
| lost response | network failure after sending | `GET /tollex/operations/{operationId}`; do not re-sign |

## Live state

- [Activity](https://tollex.org/activity/): settled operations (with Blockscout links) and rejected attempts.
- [Live Production Verification](../.github/workflows/verify-live.yml): public checks twice a day.
