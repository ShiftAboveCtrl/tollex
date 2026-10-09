# Capabilities

34 first-party capabilities are live on Robinhood Chain mainnet. Each is called with
`POST https://api.tollex.org/tools/{id}` and a JSON body that matches its input schema, paid per call in
USDG with x402 v2, and returns a result with an EIP-712 receipt. None has side effects outside Tollex: the
only funds that move are the payment for the call itself.

Prices are set per call and stated in every 402 challenge, which is authoritative. At publication every
capability was priced at 0.0082 USDG (8200 atomic units). The live catalogue at
[`/v1/catalog`](https://api.tollex.org/v1/catalog) carries full input schemas, risk metadata and receipt
capabilities for every entry.

| Category | Capabilities |
| --- | :-: |
| [Chain](#chain) | 8 |
| [Wallet](#wallet) | 5 |
| [USDG](#usdg) | 4 |
| [x402](#x402) | 7 |
| [Stock Tokens](#stock-tokens) | 5 |
| [Merchant](#merchant) | 3 |
| [Receipt](#receipt) | 2 |

## Chain

Robinhood Chain state, read at pinned blocks, with settlement assurance where it matters.

| Capability | What it returns | Inputs |
| --- | --- | --- |
| **Get block**<br>`chain_get_block` | Block header by number or tag (latest \| safe \| finalized) on Robinhood Chain, including Ethereum parent-chain L1 block number. | `block`? |
| **Get transaction**<br>`chain_get_transaction` | Transaction by hash: sender, recipient, value, nonce, type, calldata size and inclusion block. | `hash` |
| **Get receipt**<br>`chain_get_receipt` | Transaction receipt with observed settlement assurance (l2_included to l2_confirmed to parent_safe to parent_finalized), canonicality re-check and confirmations. | `hash`, `confirmations`? |
| **Get logs**<br>`chain_get_logs` | Event logs for a contract over a bounded block range (max range enforced), optionally filtered by topic0. | `address`, `fromBlock`, `toBlock`, `topic0`? |
| **Contract read**<br>`chain_contract_read` | Read-only call of one view/pure function given its human-readable ABI signature, at a pinned block. | `address`, `signature`, `args`? |
| **Simulate call**<br>`chain_simulate` | Simulate a call against current state (eth_call). Never broadcasts. Returns return data or the revert reason/selector. | `from`?, `to`, `data`, `value`? |
| **Get code**<br>`chain_get_code` | Runtime bytecode hash and size for an address; detects EIP-7702 delegated EOAs (0xef0100 prefix) and ERC-1967 proxies. | `address` |
| **Estimate gas**<br>`chain_estimate_gas` | Gas estimate plus current base fee and priority fee, with the implied maximum cost in wei. Never broadcasts. | `from`?, `to`, `data`?, `value`? |

## Wallet

Balances, allowances and authorization state for any address.

| Capability | What it returns | Inputs |
| --- | --- | --- |
| **Native ETH balance**<br>`wallet_native_balance` | ETH (gas asset) balance and transaction count of an address on Robinhood Chain. | `address` |
| **Token balance**<br>`wallet_token_balance` | ERC-20 balance (atomic units + decimals) of an address; defaults to USDG. | `address`, `token`? |
| **Allowance**<br>`wallet_allowance` | ERC-20 allowance from owner to spender (default spender: canonical Permit2). Permit2-based x402 payments need this allowance in place. | `owner`, `token`?, `spender`? |
| **EIP-3009 authorization state**<br>`wallet_authorization_state` | Whether an EIP-3009 authorization nonce has been used (authorizationState). On USDG a replayed authorization does not revert, so use this check rather than a simulation to detect consumed authorizations. | `authorizer`, `nonce`, `token`? |
| **Token activity**<br>`wallet_activity` | Recent ERC-20 Transfer events into and out of an address (default token USDG) over a bounded block window. | `address`, `token`?, `blocks`? |

## USDG

The settlement asset itself: metadata, signing domain and replay-safe authorization state.

| Capability | What it returns | Inputs |
| --- | --- | --- |
| **USDG metadata**<br>`usdg_metadata` | USDG (Paxos Global Dollar) on Robinhood Chain: address, name, symbol, decimals, total supply and current ERC-1967 implementation. | none |
| **USDG EIP-712 domain**<br>`usdg_domain` | USDG EIP-712 signing domain and on-chain DOMAIN_SEPARATOR, with a byte-for-byte reconstruction check. | none |
| **USDG capability probe**<br>`usdg_capabilities` | Live, facet-aware verification of USDG EIP-3009/EIP-2612/EIP-712 capability and x402 contract bytecode on Robinhood Chain (read-only). | none |
| **USDG authorization state**<br>`usdg_authorization_state` | authorizationState(authorizer, nonce) on USDG. This is the authoritative replay check, because USDG replays do not revert. | `authorizer`, `nonce` |

## x402

Tools for agents and operators working with x402: inspect, validate, simulate, reconcile, verify.

| Capability | What it returns | Inputs |
| --- | --- | --- |
| **Inspect x402 endpoint**<br>`x402_inspect_endpoint` | Fetch a resource unpaid (SSRF-guarded) and decode its x402 v2 challenge: resource info, accepts[], extensions, latency and accepts hash. | `url` |
| **Get payment requirements**<br>`x402_get_requirements` | FRESH payment requirements for a resource (never cached; historical listings are not payment terms). | `url` |
| **Validate requirements**<br>`x402_validate_requirements` | Validate x402 v2 payment requirements (given inline or fetched from a URL) against CAIP-2, atomic amounts, USDG domain and scheme-specific extras. | `url`?, `requirements`? |
| **Simulate payment**<br>`x402_simulate_payment` | Pre-flight a payment WITHOUT signing: requirement validity, payer USDG balance, Permit2 allowance (for Permit2/upto), and whether gas-sponsored approval is offered. | `url`?, `requirements`?, `payer` |
| **Facilitator status**<br>`x402_facilitator_status` | A facilitator's live /supported and /ready (SSRF-guarded), or the status of Tollex's configured facilitator mesh. | `url`? |
| **Reconciliation check**<br>`x402_reconcile_operation` | Read-only reconciliation check of a Tollex payment operation: durable state vs. chain evidence for its settlement transaction. | `operationId` |
| **Verify execution receipt**<br>`x402_verify_receipt` | Verify a Tollex execution receipt against trusted signer addresses (or a merchant's well-known receipt keys URL). | `receipt`, `trustedSigners`?, `keysUrl`? |

## Stock Tokens

Robinhood Stock Tokens: the official registry, quotes with halt and staleness checks, corporate actions. Price inputs only; payments always settle in USDG.

| Capability | What it returns | Inputs |
| --- | --- | --- |
| **List Stock Tokens**<br>`stock_tokens_list` | Official Robinhood Stock Token registry: symbol, name, Robinhood Chain contract, current corporate-action multiplier, status. | `limit`? |
| **Stock Token metadata**<br>`stock_token_metadata` | Registry entry for one Stock Token plus its on-chain ERC-20 metadata on Robinhood Chain. | `symbol` |
| **Stock Token quote**<br>`stock_token_quote` | Multiplier-adjusted Stock Token mid price with halt and staleness checks; returns an input hash to commit into receipts. This is a price input only; payments settle in USDG. | `symbol` |
| **Stock Token halt status**<br>`stock_token_halt_status` | Whether a Stock Token's underlying is in a trading halt, with the quote generation time. | `symbol` |
| **Stock Token corporate actions**<br>`stock_token_corporate_actions` | Processed corporate actions (splits, cash/stock dividends) that change Stock Token multipliers, optionally for one symbol. | `symbol`? |

## Merchant

Inspect any x402 merchant before paying it. Merchant metadata is treated as untrusted.

| Capability | What it returns | Inputs |
| --- | --- | --- |
| **Inspect merchant**<br>`merchant_inspect` | Inspect a merchant endpoint: live x402 terms, Tollex receipt keys, A2A agent card and MCP server card if published (all SSRF-guarded, metadata treated as untrusted). | `url` |
| **Merchant health**<br>`merchant_health` | Merchant availability: /health status, latency, and whether the resource currently answers with a valid x402 402 challenge. | `url` |
| **Merchant payment options**<br>`merchant_payment_options` | Normalised payment options for a resource: scheme, network, asset, human amount (USDG decimals), payTo, bound facilitator, gas sponsorship and receipt support. | `url` |

## Receipt

Fetch and verify Tollex execution receipts.

| Capability | What it returns | Inputs |
| --- | --- | --- |
| **Get receipt**<br>`receipt_get` | Fetch a stored Tollex execution receipt (body, content hash, signer, signature) by receipt id. | `receiptId` |
| **Verify receipt**<br>`receipt_verify` | Cryptographically verify a Tollex execution receipt against trusted signer addresses supplied by the caller. | `receipt`, `trustedSigners` |

`?` marks an optional input.

## Calling a capability

```bash
# 1. unpaid call: returns 402 with the exact terms in the PAYMENT-REQUIRED header
curl -i -X POST https://api.tollex.org/tools/wallet_token_balance \
  -H 'content-type: application/json' -d '{"address":"0x2eB98e76db13287eD4AEE5F1C7f14a7e378966B7"}'
# 2. sign an EIP-3009 authorization for those terms with any x402 v2 client and retry with PAYMENT-SIGNATURE
# 3. the 200 response carries the result and a PAYMENT-RESPONSE header with the transaction and receipt
```
