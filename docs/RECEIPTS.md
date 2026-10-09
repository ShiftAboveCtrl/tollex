# Receipts

Every paid Tollex result carries an **execution receipt**: a signed, self-contained statement of what
was requested, what was returned, what it cost and how it was paid. A receipt can be verified by anyone,
offline, without trusting Tollex.

## Format

| Property | Value |
| --- | --- |
| Signature scheme | EIP-712 typed data, secp256k1 |
| Domain | `{ name: "Tollex Execution Receipt", version: "1" }` |
| Primary type | `ExecutionReceipt(uint256 version, string receiptId, bytes32 contentHash, uint256 issuedAt)` |
| `contentHash` | keccak-256 of the RFC 8785 (JCS) canonical JSON of the receipt body; numbers are safe integers, amounts are decimal strings |
| Where to find it | `PAYMENT-RESPONSE` header, `extensions["tollex-receipt"].info`; or `GET /tollex/receipts/{receiptId}` |
| Signing keys | [`/.well-known/tollex-receipt-keys`](https://api.tollex.org/.well-known/tollex-receipt-keys) |

The signed message is deliberately small: the body is bound through `contentHash`, so the full body can
evolve with new optional fields while every signature stays verifiable.

## Body

Required fields are in **bold**.

| Field | Contents |
| --- | --- |
| **`version`** | body version (`1` or `2`) |
| **`receiptId`** | unique receipt identifier |
| **`operationId`** | the payment operation this result belongs to (`GET /tollex/operations/{operationId}`) |
| **`issuedAt`** | issue time (Unix seconds) |
| **`resource`** | `{ id, method, url }` of the capability called |
| **`requestHash`** | hash of the canonical request |
| `responseHash`, `responseStatus` | hash of the response body and its HTTP status |
| **`pricingTermsHash`** | hash of the pricing terms the agent was offered |
| **`paymentRequirementsHash`** | hash of the x402 requirements in the 402 challenge |
| `meteringHash`, `pricingInputs` | inputs used to compute the price, where applicable |
| **`payment`** | `{ scheme, network, asset, payer, payTo, authorizedAmount, actualAmount, authorizationId }` |
| **`facilitator`** | `{ id, signer }`: which facilitator verified and settled |
| **`settlement`** | `{ state, assurance, transaction, blockNumber, blockHash, submittedAt, includedAt }` |
| **`execution`** | `{ startedAt, completedAt }` |
| `tool` | `{ id, version, providerId, definitionHash }`: the exact capability definition |
| `quote` | `{ quoteId, quoteHash, quotedAmount, inputHash }` when the call followed a quote |
| `stateFlags` | `{ charged, executed, pending, settlementFinal, refunded }` |
| `evidenceRef`, `supersedes` | link to supporting evidence; the receipt this one replaces (for example after finality) |

### Settlement assurance

`settlement.assurance` records how final the payment was when the receipt was issued, from weakest to
strongest: `l2_included`, `l2_confirmed`, `parent_safe`, `parent_finalized`. A later receipt may
`supersede` an earlier one as assurance increases.

## Verifying a receipt

1. **Canonicalise** the body with RFC 8785 (JCS) and compute keccak-256: this must equal `contentHash`.
2. **Recover** the EIP-712 signer of `{ version, receiptId, contentHash, issuedAt }` under the Tollex
   domain.
3. **Check** that the signer is an `active` key in
   [`/.well-known/tollex-receipt-keys`](https://api.tollex.org/.well-known/tollex-receipt-keys)
   (currently `0x69d778C105b7f94Bde775d7ae94F1daa56DAA88F`, key id `rk-69d778c1`).
4. **Confirm** the payment on chain: `settlement.transaction` must be a successful USDG transfer from
   `payment.payer` to `payment.payTo` of `payment.actualAmount`.
5. **Compare** `requestHash` and `responseHash` with what you sent and received.

The `receipt_verify` and `x402_verify_receipt` capabilities perform steps 1 to 3 as a service, against
signer addresses you supply.

## Why the receipt signer holds nothing

The receipt key signs statements, never transactions. It holds no ETH and no USDG, and it cannot move
funds; its only power is to attest. Keeping it separate from the relayer and the treasury means a
problem in one duty cannot be used to forge another.
