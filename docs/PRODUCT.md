# Product

Tollex is an economic control plane for autonomous software: the layer that decides whether an agent's
paid call may happen, what it costs, how it is paid, and how the result is proven afterwards.

## Who it is for

- **Agent developers** who want their agents to buy narrowly scoped capabilities per call, without
  accounts, API keys or monthly plans, and with a verifiable record of every purchase.
- **Operators** who need spending to stay inside a policy: approval thresholds, per-request ceilings and
  budgets enforced before money moves.
- **Merchants** who want to sell to agents over an open payment protocol and settle in a stable asset.

## What an agent gets

| Step | Surface | Cost |
| --- | --- | --- |
| Discover capabilities | descriptor, OpenAPI, `llms.txt`, catalogue, A2A card | free |
| Plan a call | `POST /v1/resolve` (also an A2A skill) | free, never spends |
| Get exact terms | HTTP 402 challenge (x402 v2) | free |
| Execute | the same request with a signed USDG authorization | the quoted price |
| Prove it | EIP-712 receipt, operation status, receipt lookup | free |

## Capabilities at launch

34 first-party capabilities, each with a JSON Schema for its input and a per-call USDG price:

- **chain**: blocks, transactions, receipts, logs, contract reads, simulation, code, gas estimates
- **wallet**: native and token balances, allowances, authorization state, activity
- **usdg**: token metadata, EIP-712 domain, capabilities, authorization state
- **x402**: inspect an endpoint, fetch and validate requirements, simulate a payment, facilitator
  status, reconcile an operation, verify a receipt
- **stock-token**: listings, metadata, quotes, halt status, corporate actions
- **merchant**: inspection, health, payment options
- **receipt**: fetch and verify Tollex receipts

The live catalogue at `https://api.tollex.org/v1/catalog` is authoritative.

## Pricing

Prices are per call, in USDG, and are stated in each 402 challenge. A price is never changed after a
payment has been authorized. Prices are kept above the on-chain cost of settling the payment; if
network gas rises sharply, new paid calls pause (HTTP 503 `paid_calls_paused`, nothing charged) rather
than settle at a loss. Planning, discovery and receipt verification are free.

## Not in the initial launch

- Paying external third-party x402 merchants on mainnet through Tollex (disabled by design for now).
- A production MCP endpoint (not advertised at this time).
- Published client packages.
