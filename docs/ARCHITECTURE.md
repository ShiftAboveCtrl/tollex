# Architecture

This page describes the layers of Tollex and how a paid call moves through them. It intentionally
stays at the level needed to understand and verify the service; implementation details are
proprietary.

## Layers

```
 agent
   |  discovery (descriptor, OpenAPI, llms.txt, catalogue, A2A card)      free
   |  planning  (resolve)                                                 free
   v
 +-----------------------------+
 | policy                      |  is this call allowed, at what price, under which limits
 +-----------------------------+
 | capability service          |  402 challenge with exact terms; runs the capability once paid
 +-----------------------------+
 | facilitator (x402 native)   |  verifies the payment authorization; settles it on chain
 +-----------------------------+
 | relayer                     |  submits the settlement transaction and pays its gas
 +-----------------------------+
 | receipts                    |  EIP-712 receipt bound to request, response and payment
 +-----------------------------+
 | reconciliation              |  confirms every settlement on chain and matches it to its operation
 +-----------------------------+
   |
   v
 Robinhood Chain mainnet (USDG, EIP-3009)
```

Each layer has one job and its own failure behaviour:

| Layer | Key or identity | On failure |
| --- | --- | --- |
| Policy | none | refuses the call before any payment is requested |
| Capability service | none that can move funds | no result is delivered without a settled payment |
| Facilitator | none of its own; uses the relayer | refuses to verify or settle |
| Relayer | relayer address (holds ETH for gas only) | stops signing; nothing is broadcast |
| Receipts | receipt signer (holds nothing) | the call is not reported as complete |
| Reconciliation | none | flags the operation; alerts the operator |

## A paid call

1. The agent sends a request to a capability without payment.
2. Policy admits the call and fixes the price; the service answers `402 Payment Required` with an x402
   v2 challenge: network `eip155:4663`, asset USDG, amount, recipient, validity window, Bazaar metadata
   and the receipt extension.
3. The agent signs an EIP-3009 `transferWithAuthorization` for exactly those terms and retries.
4. The facilitator verifies the authorization against the challenge (amount, recipient, asset,
   network, validity, nonce, payer balance) and settles it. The relayer submits the transaction; the
   USDG contract moves the funds directly from the payer to the treasury and marks the authorization as
   used, so it cannot be replayed.
5. The capability runs once, and the response carries a `PAYMENT-RESPONSE` header with the
   transaction hash and a signed receipt.
6. Reconciliation confirms inclusion on chain and binds the transaction to the operation.

## Separation of funds

The relayer never holds the payment asset and never receives payments; it only pays gas. Payments
move from the payer to the treasury inside the token contract. The receipt signer never holds funds.
The four public identities are listed in [evidence/mainnet-launch.public.json](../evidence/mainnet-launch.public.json).

## Hosting

Production runs as containers from a pinned image digest behind Cloudflare, with a managed PostgreSQL
database (encrypted, private, TLS with certificate and hostname verification), two independent RPC
providers for Robinhood Chain, non-exportable keys in a managed hardware-backed key service, and
continuous health checks and alerting.
