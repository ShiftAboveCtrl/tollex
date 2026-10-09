#!/usr/bin/env bash
# Try Tollex in 60 seconds with curl + jq. Nothing here signs or spends.
set -euo pipefail
API=${TOLLEX_URL:-https://api.tollex.org}

echo "== 1. discover"
curl -s "$API/.well-known/tollex.json" | jq '{name, network: .payment.networks, asset: .payment.assets[0], capabilities: .capabilities.count}'

echo "== 2. plan for free (which capability fits, what it costs)"
curl -s -X POST "$API/v1/resolve" -H 'content-type: application/json' \
  -d '{"need":"USDG balance of an address","input":{"address":"0x2eB98e76db13287eD4AEE5F1C7f14a7e378966B7"}}' \
  | jq '.plan | {selected: .selected.toolId, eligible, candidates}'

echo "== 3. exact payment terms (an unpaid call returns HTTP 402)"
curl -s -D - -o /dev/null -X POST "$API/tools/wallet_token_balance" -H 'content-type: application/json' \
  -d '{"address":"0x2eB98e76db13287eD4AEE5F1C7f14a7e378966B7"}' \
  | grep -i '^payment-required:' | cut -d' ' -f2 | tr -d '\r' \
  | jq -R '@base64d | fromjson | .accepts[0] | {scheme, network, asset, amount, payTo, maxTimeoutSeconds, usdgDomain: .extra}'

echo "== 4. verify a real receipt (the first mainnet settlement)"
curl -s "$API/tollex/receipts/rcpt_i-xD2HIyq46pjn0z" | jq '{receiptId: .body.receiptId, signer, transaction: .body.settlement.transaction, assurance: .body.settlement.assurance}'
curl -s "$API/.well-known/tollex-receipt-keys" | jq '.keys[] | {address, status}'
echo "   explorer: https://robinhoodchain.blockscout.com/tx/0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533"

echo "== 5. ask as an agent (A2A, free planning)"
curl -s -X POST "$API/a2a" -H 'content-type: application/json' -H 'a2a-version: 1.0' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"role":"ROLE_USER","messageId":"curl-1","parts":[{"data":{"skill":"tollex.resolve_intent","need":"latest block header on Robinhood Chain"}}]}}}' \
  | jq '.result.task.status.state'
