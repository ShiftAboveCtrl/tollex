# Glossary

| Term | Meaning in Tollex |
| --- | --- |
| **A2A** | Agent-to-Agent protocol. Tollex publishes an agent card and a JSON-RPC endpoint so other agents can plan with it. |
| **Atomic units** | The smallest unit of USDG (6 decimals): 1,000,000 atomic units = 1 USDG. Prices and amounts are stated in atomic units. |
| **Bazaar metadata** | An x402 challenge extension that describes the capability and its input and output schema, for x402 discovery catalogues. |
| **CAIP-2** | Chain identifier format. Robinhood Chain mainnet is `eip155:4663`. |
| **Canary** | A single, operator-approved, minimal payment through the full public payment path, used to prove a release on mainnet. Not scheduled. |
| **Capability** | A paid operation Tollex sells, called at `/tools/{id}`, described by a JSON Schema. |
| **Control plane** | The layer that decides whether a paid call may happen, what it costs, how it is paid and how it is proven, as opposed to the capability that does the work. |
| **EIP-3009** | `transferWithAuthorization`: a signed, single-use authorization that lets a token move an exact amount from payer to recipient without the payer sending a transaction. |
| **EIP-712** | Structured-data signing. Used for payment authorizations and for Tollex receipts. |
| **Facilitator** | The x402 component that verifies a payment authorization against the challenge and settles it on chain. Tollex runs its own. |
| **Operation** | The durable record of one paid call: challenge, payment, settlement, execution, receipt. |
| **Policy** | The rules evaluated before a payment is requested: eligibility, ceilings, approvals, budgets. |
| **Price floor** | The minimum price that still covers on-chain settlement cost plus margin. Prices never go below it; new paid calls pause if it rises beyond tolerance. |
| **Receipt** | An EIP-712 signature over the canonical hash of a result's request, response, price and settlement. See [RECEIPTS](RECEIPTS.md). |
| **Reconciliation** | Confirming each settlement on chain and binding it to its operation; the chain is the source of truth. |
| **Relayer** | The identity that submits settlement transactions and pays their gas. It holds ETH only and never receives payments. |
| **Resolve** | The free planning step: given a need, Tollex returns the eligible capabilities, the selected one and its terms. |
| **Robinhood Chain** | The network Tollex settles on: an Ethereum layer 2, chain id 4663. |
| **Treasury** | The address that receives payments for Tollex capabilities. |
| **USDG** | Global Dollar, the stablecoin Tollex settles in on Robinhood Chain (`0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`). |
| **x402** | An open protocol for HTTP-native payments: a server answers `402 Payment Required` with machine-readable terms; the client pays and retries. Tollex implements version 2. |
