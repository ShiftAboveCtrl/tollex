# Changelog

Public milestones of the Tollex production service.

## 2026-10-10: USDC on Base as a second payment rail

- Every capability is now payable with x402 v2 `exact` in **USDC on Base** (`eip155:8453`) or **USDG on Robinhood
  Chain** (`eip155:4663`), at the same price. The `402` lists one option per rail; standard `@x402` clients pay Base
  USDC with their default settings.
- Base payments are settled by an x402 facilitator and confirmed on Base by Tollex (transaction succeeded, this
  authorization consumed, exact amount from the payer to the treasury) before any result is released. Receipts are
  signed by the same published key and record the payment network.
- `GET /v1/agent-check`: the first paid call (about 0.008 USD) to verify an integration end to end.
- Standard x402 discovery: `/.well-known/x402` and OpenAPI `x-payment-info`.
- Examples: `--rail base|robinhood`, `first-payment`, spend policy (per call, per session, allowed rails).

## 2026-10-09: Developer onboarding

- [QUICKSTART](docs/QUICKSTART.md) and [AGENTS.md](AGENTS.md) for developers and coding agents.
- Runnable examples against production: curl, TypeScript (`@x402/fetch` 2.28), Python, A2A, LangChain /
  LangGraph, CrewAI and Google ADK, each with receipt verification and payment guarded by an explicit ceiling.
- Every settled transaction on [tollex.org/activity](https://tollex.org/activity/) links to Blockscout.

## 2026-10-08: Public documentation

- Expanded documentation: receipts reference, full capability reference, glossary, architecture and
  launch-proof diagrams.
- Live status badges sourced directly from the production service.

## 2026-10-08: Robinhood Chain mainnet launch

- Production service live at `https://api.tollex.org` on Robinhood Chain mainnet (`eip155:4663`).
- Native x402 v2 facilitator settling USDG payments with EIP-3009 authorizations.
- First mainnet settlement: [`0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533`](https://robinhoodchain.blockscout.com/tx/0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533) ([Blockscout](https://robinhoodchain.blockscout.com/tx/0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533))
  (block 83335219, 0.001 USDG, all launch checks passed).
- Release `0.2.0`, source commit `abff565c2188`, image `sha256:ba35243f...678ae`, deployed only after
  owner approval of the exact release.
- Public discovery: descriptor, OpenAPI 3.1, `llms.txt`, catalogue, A2A agent card, receipt keys,
  x402 challenges with Bazaar metadata.
- External third-party mainnet routing disabled for the initial launch.
- This verification repository and its scheduled public verification workflow.
