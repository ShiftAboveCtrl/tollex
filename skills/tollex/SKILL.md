---
name: tollex
description: Buy a paid capability from Tollex over x402 (USDC on Base or USDG on Robinhood Chain) and verify its signed receipt. Use when the user wants on-chain data for Robinhood Chain (blocks, logs, balances, Stock Token prices and halt status, eth_call simulation), wants to inspect another x402 endpoint's live payment terms, or wants to test that an agent wallet can make and verify one real x402 payment.
---

# Tollex: plan for free, pay per call, verify the receipt

Tollex (https://api.tollex.org) sells capabilities to agents over x402 v2 (`exact`, EIP-3009). Planning is free;
each paid call costs about 0.008 USD (the live `402` is authoritative) and returns the result with an EIP-712
receipt signed by a key published at `https://api.tollex.org/.well-known/tollex-receipt-keys`.

## Rules (money moves: follow these exactly)

1. Never pay without a per-call ceiling the **user** gave you, in atomic units (6 decimals; 10000 = 0.01 USD).
   Never choose a ceiling yourself.
2. Ask the user before each payment unless they explicitly enabled autonomous payment with that ceiling.
3. The private key comes only from the `TOLLEX_PRIVATE_KEY` environment variable the user set. Never ask the
   user to paste a key into the chat, never print it, never write it to a file.
4. A `402` with `invalid_exact_evm_*` means nothing moved. A `202` means settlement is pending: resend the SAME
   request later; never sign a second authorization for it.

## Free steps (no wallet)

```bash
# which capability fits a need (never spends)
curl -s https://api.tollex.org/v1/resolve -H 'content-type: application/json' -d '{"need":"latest block on Robinhood Chain"}'
# all capabilities, input schemas, prices
curl -s https://api.tollex.org/v1/catalog
# the payment terms of one call: read the PAYMENT-REQUIRED header (base64 JSON, one option per rail)
curl -s -D - -o /dev/null -X POST https://api.tollex.org/tools/chain_get_block -H 'content-type: application/json' -d '{"block":"latest"}' | grep -i '^payment-required:'
```

## Paid call (one command, with the user's ceiling)

Requires `uv`. The script signs ONE authorization for exactly the quoted amount, refuses above `--max`, prints the
Blockscout link and verifies the receipt.

```bash
A=https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/examples/agent-check/agent_check.py
uv run $A                                   # price on each rail, nothing signed
uv run $A --pay --max <CEILING>             # first paid call: GET /v1/agent-check, USDC on Base
uv run $A --rail robinhood --pay --max <CEILING>
uv run $A --tool stock_token_quote --input '{"symbol":"AAPL"}' --pay --max <CEILING>
uv run $A --tool x402_inspect_endpoint --input '{"url":"https://example.com/paid"}' --pay --max <CEILING>
uv run $A --tool chain_simulate --input '{"to":"0x...","data":"0x..."}' --pay --max <CEILING>
```

`TOLLEX_PRIVATE_KEY` must already be set in the environment for `--pay`. Pick the rail the wallet holds:
`base` (USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, `eip155:8453`) or `robinhood` (USDG
`0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, `eip155:4663`). If it holds neither, stop and tell the user.

Any x402 v2 client works instead of the script (`@x402/fetch`, x402 Python, `npx x402-proxy --network base <url>`):
Base USDC is a default asset there; set a spend cap.

## Report back to the user

The result, the rail paid on, the Blockscout transaction link from `PAYMENT-RESPONSE`, and whether the receipt
verified. The operation also appears, without wallet identity, on https://tollex.org/activity/.

## More

- Full agent instructions, outcomes table, receipt verification: https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/AGENTS.md
- Five good first capabilities: https://github.com/ShiftAboveCtrl/tollex/blob/main/docs/TRY.md
- Problems: https://github.com/ShiftAboveCtrl/tollex/discussions
