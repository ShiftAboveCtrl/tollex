# Tollex

**A production economic control plane for autonomous software.** Tollex lets software agents discover
paid capabilities, plan a call without spending, pay per call in USDG over
[x402](https://www.x402.org/), and receive a signed receipt for every result. It runs its own native
x402 facilitator and is live on **Robinhood Chain mainnet** (`eip155:4663`).

| | |
| --- | --- |
| Status | Live on mainnet since 2026-10-08 ([launch record](docs/MAINNET_LAUNCH.md)) |
| API | https://api.tollex.org |
| Network | Robinhood Chain mainnet, `eip155:4663` |
| Asset | USDG `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168` (6 decimals) |
| Payment protocol | x402 v2, `exact` scheme (EIP-3009 authorizations) |
| First settlement | [`0x82f1c72c...1c533`](evidence/mainnet-launch.public.json), block 83335219 |
| Security contact | security@tollex.org ([SECURITY.md](SECURITY.md)) |

> This repository holds public documentation and independent verification material. It does **not**
> contain the Tollex implementation, which is proprietary. See [NOTICE](NOTICE).

## What Tollex does

An agent that needs something done (read chain state, check a wallet, inspect an x402 merchant,
verify a receipt) can:

1. **Discover** what Tollex offers from machine-readable surfaces: a descriptor, an OpenAPI 3.1
   document, `llms.txt`, a catalogue and an A2A agent card.
2. **Plan** with a free resolve step that says which capability fits and what it will cost. Planning
   never spends.
3. **Pay** per call. An unpaid request receives an HTTP 402 challenge with exact terms; the agent signs
   a USDG authorization and retries.
4. **Receive** the result with an EIP-712 receipt signed by a published key, bound to the request,
   the response and the payment.

Policy, routing, settlement, receipts and reconciliation are separate layers with separate keys and
separate failure behaviour ([architecture](docs/ARCHITECTURE.md)).

## Initial launch scope

- 34 first-party capabilities across chain, wallet, USDG, x402, merchant, receipt and stock-token
  categories, served and settled on Robinhood Chain mainnet.
- Routing calls to **external third-party x402 merchants on mainnet is intentionally disabled** for the
  initial launch. It will be enabled separately, with its own controls, after launch.
- An MCP endpoint is not advertised in production at this time; discovery reports exactly what is
  served.

## Verify it yourself

Everything below uses public information only and never pays.

```bash
git clone https://github.com/ShiftAboveCtrl/tollex.git && cd tollex
scripts/verify-live.sh           # public API surfaces
scripts/verify-live.sh --chain   # plus the launch settlement, read from a public Robinhood Chain RPC
```

The [Live Production Verification](.github/workflows/verify-live.yml) workflow runs the same checks on
a schedule. Step-by-step manual checks are in [docs/VERIFY.md](docs/VERIFY.md).

## Documentation

| Document | Contents |
| --- | --- |
| [PRODUCT](docs/PRODUCT.md) | What Tollex offers and to whom |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | The layers and how a paid call flows through them |
| [X402](docs/X402.md) | How Tollex speaks x402 v2 on Robinhood Chain |
| [AGENT_DISCOVERY](docs/AGENT_DISCOVERY.md) | Machine-to-machine discovery surfaces |
| [SECURITY_MODEL](docs/SECURITY_MODEL.md) | Custody, separation of duties and fail-closed controls |
| [MAINNET_LAUNCH](docs/MAINNET_LAUNCH.md) | The launch procedure and its evidence |
| [VERIFY](docs/VERIFY.md) | Independent verification, by hand or with the script |
| [CHANGELOG](CHANGELOG.md) | Public milestones |

## License

Proprietary. All rights reserved. Publication of this repository does not grant any right to
reproduce, reimplement or redistribute Tollex. See [NOTICE](NOTICE).
