# Security model

How Tollex protects funds and keeps its promises to agents, at the level needed to evaluate it.
Reports go to security@tollex.org ([SECURITY.md](../SECURITY.md)).

## Custody

- Signing keys are non-exportable keys in a managed hardware-backed key service. Production services
  request signatures; no private key exists in an image, a configuration file or a database.
- Four separate identities, each with a single purpose:

| Identity | Holds | Signs |
| --- | --- | --- |
| Relayer | ETH for gas only, capped | settlement transactions |
| Receipt signer | nothing, by policy | EIP-712 receipts |
| Treasury | received payments | nothing in normal operation |
| Canary payer | a small operator test balance | operator test payments only |

- Payers never give Tollex custody: an EIP-3009 authorization moves an exact amount once, to the
  stated recipient, within a validity window.

## Release control

Mainnet writes are enabled only for an exact release: a manifest binding the source commit, the image
digest, the configuration and the policies, signed by the owner. Production runs a pinned image
digest, never a mutable tag.

## Fail-closed controls

| Condition | Behaviour |
| --- | --- |
| Payment does not match the challenge | refused before the capability runs; nothing charged |
| Authorization already used | refused (the token contract records each authorization) |
| Settlement gas rises beyond the price tolerance | new paid calls pause; nothing charged |
| Relayer balance below its minimum | relayer refuses to sign |
| Daily gas budget spent | relayer not ready until the window rolls |
| Per-transaction gas limit or fee ceiling exceeded | transaction not sent |
| On-chain contract code differs from the pinned version | the affected path is disabled |
| RPC providers disagree | treated as unsafe; alert |
| Writes switch disabled | every payment refused; discovery stays up |

Public endpoints are rate limited. Anonymous callers cannot cause the relayer to spend gas: a
transaction is only sent for a verified authorization that pays at least the quoted price.

## Operations

- Separate production database credentials with least privilege; database connections require TLS
  with certificate and hostname verification.
- Health checks, readiness checks and alerting on relayer balance, gas budget, signer failures,
  settlement failures, reconciliation lag, RPC disagreement, replay attempts and service availability.
- An emergency stop returns production to read-only (discovery up, all payments refused) in one
  operator action.

## Scope of the initial launch

Calls to external third-party x402 merchants on mainnet are disabled. Only Tollex first-party
capabilities are sold and settled on mainnet.
