#!/usr/bin/env bash
# Independent verification of Tollex production using public information only.
#
#   scripts/verify-live.sh            public API surfaces on https://api.tollex.org
#   scripts/verify-live.sh --chain    also the launch settlement, read from a public Robinhood Chain RPC
#
# Requires bash, curl and jq (1.6 or later). Read-only: it never signs, pays or writes anything.
# An unpaid request to a paid capability is answered with an x402 payment challenge and is not charged.
set -uo pipefail

API="${TOLLEX_API:-https://api.tollex.org}"
RPC="${ROBINHOOD_RPC:-https://rpc.mainnet.chain.robinhood.com}"
EVIDENCE="$(cd "$(dirname "$0")/.." && pwd)/evidence/mainnet-launch.public.json"

NETWORK="eip155:4663"
USDG="0x5fc5360d0400a0fd4f2af552add042d716f1d168"
BASE_NETWORK="eip155:8453"
BASE_USDC="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
RECEIPT_SIGNER="0x69d778c105b7f94bde775d7ae94f1daa56daa88f"
RELAYER="0xcbe1b48c188edf24b3c939e46647a80fb9f75645"
CANARY_PAYER="0x488bf1856c50ec965b13d8e745ff31f6b1fc4841"
TREASURY="0x2eb98e76db13287ed4aee5f1c7f14a7e378966b7"
LAUNCH_TX="0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533"
LAUNCH_BLOCK=83335219

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
pass=0; fail=0; warn=0
ok()   { pass=$((pass + 1)); printf 'PASS  %-34s %s\n' "$1" "$2"; }
bad()  { fail=$((fail + 1)); printf 'FAIL  %-34s %s\n' "$1" "$2"; }
note() { warn=$((warn + 1)); printf 'WARN  %-34s %s\n' "$1" "$2"; }
lc()   { tr '[:upper:]' '[:lower:]'; }
get()  { curl -sS --max-time 20 -A "tollex-public-verify/1" -o "$TMP/body" -w '%{http_code}' "$@" 2>/dev/null || echo 000; }

check_json() { # name path jq-filter-that-must-be-true detail-filter
  local code; code=$(get "$API$2")
  if [ "$code" != 200 ]; then bad "$1" "HTTP $code"; return; fi
  if jq -e "$3" "$TMP/body" >/dev/null 2>&1; then ok "$1" "$(jq -r "$4" "$TMP/body" 2>/dev/null)"; else bad "$1" "unexpected content"; fi
}

echo "Tollex public verification: $API ($(date -u +%Y-%m-%dT%H:%M:%SZ))"

check_json "readiness /ready" /ready '.ready == true' '"ready"'

check_json "descriptor /.well-known/tollex.json" /.well-known/tollex.json \
  ".name == \"Tollex\" and .payment.protocol == \"x402\" and .payment.x402Version == 2
   and (.payment.networks | index(\"$NETWORK\")) != null
   and any(.payment.assets[]; .network == \"$NETWORK\" and (.address | ascii_downcase) == \"$USDG\")" \
  '"x402 v\(.payment.x402Version) on \(.payment.networks | join(",")), \(.capabilities.count) capabilities"'

check_json "OpenAPI /openapi.json" /openapi.json '(.openapi | startswith("3.1")) and (.paths | length) > 0' \
  '"OpenAPI \(.openapi), \(.paths | length) paths"'

code=$(get "$API/llms.txt")
if [ "$code" = 200 ] && head -1 "$TMP/body" | grep -q '^# Tollex'; then ok "llms.txt /llms.txt" "$(wc -l < "$TMP/body" | tr -d ' ') lines"; else bad "llms.txt /llms.txt" "HTTP $code"; fi

check_json "catalog /v1/catalog" /v1/catalog \
  "(.tools | length) > 0 and any(.tools[]; .id == \"chain_get_block\")" \
  '"\(.tools | length) capabilities"'

check_json "receipt keys" /.well-known/tollex-receipt-keys \
  "any(.keys[]; .status == \"active\" and (.address | ascii_downcase) == \"$RECEIPT_SIGNER\")" \
  '"active: \([.keys[] | select(.status == "active") | .address] | join(","))"'

check_json "A2A agent card" /.well-known/agent-card.json 'any(.skills[]; .id == "tollex.resolve_intent")' \
  '"\(.skills | length) skills"'

# A2A: a planning request is free and never spends.
code=$(get -X POST "$API/a2a" -H 'content-type: application/json' -H 'a2a-version: 1.0' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"role":"ROLE_USER","messageId":"public-verify","parts":[{"data":{"skill":"tollex.resolve_intent","need":"latest block header on Robinhood Chain"}}]}}}')
if [ "$code" = 200 ] && jq -e '.result.task.status.state == "TASK_STATE_COMPLETED"' "$TMP/body" >/dev/null 2>&1; then
  ok "A2A plan (free)" "task completed"
else bad "A2A plan (free)" "HTTP $code"; fi

# x402: an unpaid call to a paid capability must return a payment challenge on Robinhood Chain in USDG.
code=$(curl -sS --max-time 20 -A "tollex-public-verify/1" -D "$TMP/headers" -o "$TMP/body" -w '%{http_code}' \
  -X POST "$API/tools/chain_get_block" -H 'content-type: application/json' -d '{"block":"latest"}' 2>/dev/null || echo 000)
if [ "$code" = 402 ]; then
  pr=$(grep -i '^payment-required:' "$TMP/headers" | head -1 | cut -d' ' -f2- | tr -d '\r')
  if [ -n "$pr" ] && printf '%s' "$pr" | jq -R '@base64d | fromjson' > "$TMP/pr" 2>/dev/null \
     && jq -e ".x402Version == 2 and (.accepts | length) > 0
               and any(.accepts[]; .network == \"$NETWORK\" and (.asset | ascii_downcase) == \"$USDG\")
               and all(.accepts[]; ((.network == \"$NETWORK\" and (.asset | ascii_downcase) == \"$USDG\") or (.network == \"$BASE_NETWORK\" and (.asset | ascii_downcase) == \"$BASE_USDC\"))
                                   and (.payTo | ascii_downcase) == \"$TREASURY\" and (.amount | test(\"^[1-9][0-9]*$\")))
               and .extensions.bazaar.info != null and .extensions.bazaar.schema != null" "$TMP/pr" >/dev/null; then
    ok "x402 challenge + Bazaar" "$(jq -r '[.accepts[] | "\(.amount) atomic on \(.network)"] | join(", ") + ", payTo treasury"' "$TMP/pr")"
  else bad "x402 challenge + Bazaar" "challenge missing or unexpected"; fi
elif [ "$code" = 503 ] && jq -e '.error == "paid_calls_paused" and .charged == false' "$TMP/body" >/dev/null 2>&1; then
  # Fail-closed by design: settlement gas rose beyond the price tolerance, so new paid calls wait.
  note "x402 challenge + Bazaar" "paid calls paused by the gas-price floor (fail closed, nothing charged)"
else bad "x402 challenge + Bazaar" "HTTP $code"; fi

if [ "${1:-}" = "--chain" ]; then
  rpc() { curl -sS --max-time 20 -H 'content-type: application/json' -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"$1\",\"params\":$2}" "$RPC" 2>/dev/null; }
  chain=$(rpc eth_chainId '[]' | jq -r '.result // empty')
  if [ "$chain" = "0x1237" ]; then ok "chain id" "4663"; else bad "chain id" "${chain:-no answer}"; fi
  rpc eth_getTransactionReceipt "[\"$LAUNCH_TX\"]" > "$TMP/rcpt"
  rpc eth_getTransactionByHash "[\"$LAUNCH_TX\"]" > "$TMP/tx"
  TRANSFER=0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
  AUTH_USED=0x98de503528ee59b575ef0c0a2576a82497bfc029a5685b209e9ec333479b10a5
  pad() { printf '0x000000000000000000000000%s' "${1#0x}"; }
  if jq -e ".result.status == \"0x1\" and (.result.blockNumber | ltrimstr(\"0x\")) == \"$(printf '%x' $LAUNCH_BLOCK)\"
            and (.result.from | ascii_downcase) == \"$RELAYER\" and (.result.to | ascii_downcase) == \"$USDG\"" "$TMP/rcpt" >/dev/null 2>&1; then
    ok "launch tx receipt" "success in block $LAUNCH_BLOCK, sent by the relayer to USDG"
    echo "      explorer: https://robinhoodchain.blockscout.com/tx/$LAUNCH_TX"
  else bad "launch tx receipt" "unexpected or unavailable"; fi
  if jq -e "any(.result.logs[]; (.address | ascii_downcase) == \"$USDG\" and .topics[0] == \"$TRANSFER\"
            and .topics[1] == \"$(pad $CANARY_PAYER)\" and .topics[2] == \"$(pad $TREASURY)\"
            and (.data | ltrimstr(\"0x\") | ltrimstr(\"0\" * 61)) == \"3e8\")
            and any(.result.logs[]; .topics[0] == \"$AUTH_USED\")" "$TMP/rcpt" >/dev/null 2>&1; then
    ok "launch transfer" "1000 atomic USDG canary payer -> treasury; authorization marked used"
  else bad "launch transfer" "Transfer or AuthorizationUsed log not as published"; fi
  if jq -e '.result.input | startswith("0xe3ee160e")' "$TMP/tx" >/dev/null 2>&1; then
    ok "launch method" "transferWithAuthorization (EIP-3009)"
  else bad "launch method" "unexpected calldata"; fi
  if [ -f "$EVIDENCE" ]; then
    gas=$(jq -r '.result.gasUsed' "$TMP/rcpt"); want=$(jq -r '.transaction.gasUsed' "$EVIDENCE")
    if [ -n "$gas" ] && [ "$((gas))" = "$want" ]; then ok "evidence matches chain" "gasUsed $want"; else bad "evidence matches chain" "gasUsed ${gas:-?} vs $want"; fi
  fi
fi

echo "summary: $pass passed, $warn warnings, $fail failed"
[ "$fail" -eq 0 ]
