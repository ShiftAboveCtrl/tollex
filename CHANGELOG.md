# Changelog

Public milestones of the Tollex production service.

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
