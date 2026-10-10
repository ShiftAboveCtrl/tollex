# Try a real mainnet call

**Can your agent buy its first verified result?** No signup, no sandbox, no testnet: one real x402 payment of
about 0.008 USD, a real result, a signed receipt anyone can verify, and a privacy-safe entry on
[tollex.org/activity](https://tollex.org/activity/).

You need a wallet holding a little **USDC on Base** (or USDG on Robinhood Chain). Nothing else.

## One command

```bash
# see the price on each rail (nothing signed)
uv run https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/examples/agent-check/agent_check.py

# pay at most 0.01 USDC on Base, print the result, verify the receipt
TOLLEX_PRIVATE_KEY=0x... uv run https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/examples/agent-check/agent_check.py --pay --max 10000
```

Already using [x402-proxy](https://github.com/cascade-protocol/x402-proxy) with a Base wallet:

```bash
npx x402-proxy --network base https://api.tollex.org/v1/agent-check
```

Any x402 v2 client works: `GET https://api.tollex.org/v1/agent-check`, read the `402`, pay the `eip155:8453` USDC
option. With `@x402/fetch` that is a wallet and the default spend controls. More: [QUICKSTART](QUICKSTART.md),
[TypeScript](../examples/typescript/), [Python](../examples/python/), [A2A](../examples/a2a/a2a_tollex.py),
[LangGraph](../examples/langgraph/), [CrewAI](../examples/crewai/), [Google ADK](../examples/google-adk/).

**Coding agent?** Paste: *"Make one real x402 payment to `GET https://api.tollex.org/v1/agent-check` with my Base
USDC wallet, never above 10000 atomic units, then verify the receipt as described in
https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/AGENTS.md."*

## What you get back

`/v1/agent-check` returns which rail you paid on, the live state of every payment rail and the current chain heads
(from Tollex's own chain views), plus links to your operation. The `PAYMENT-RESPONSE` header carries the
settlement transaction (view it on Blockscout) and an EIP-712 receipt signed by a key published at
`/.well-known/tollex-receipt-keys`. The script verifies it for you.

## Five capabilities worth a first call

Each costs the same as the first call (0.0079 USD today; the live `402` is authoritative) and is bought with the same
command: add `--tool <id> --input '<json>'`.

| Capability | What it does | Why an agent cares | Expected result | What the receipt proves |
| --- | --- | --- | --- | --- |
| `GET /v1/agent-check` | First paid call | Proves your wallet, signing and receipt handling work end to end | `paidWith`, `rails[]`, `chains{}`, `verify{}` | You paid exactly this amount on this rail and Tollex delivered |
| `x402_inspect_endpoint` | Fetches any x402 URL unpaid and decodes its v2 challenge | Check a counterparty's live terms (network, asset, payTo, amount) before your agent pays it, or monitor your own endpoint | `payable`, `httpStatus`, `accepts[]`, `extensions`, `latencyMs`, `acceptsHash` | What that endpoint advertised at that moment (hash of its accepts) |
| `stock_token_quote` | Multiplier-adjusted mid price of a Robinhood Chain Stock Token, with halt and staleness checks | A price input for trading, accounting or research agents, adjusted for splits and halts | `symbol`, `price`, `currentMultiplier`, `generatedAt`, `source` | The exact price input and its source time (input hash bound in the receipt) |
| `stock_token_halt_status` | Whether a Stock Token's underlying is halted | Do not trade into a halt | `symbol`, `isTradingHalt`, `generatedAt` | The halt state you acted on, and when |
| `chain_simulate` | `eth_call` on Robinhood Chain against current state; never broadcasts | Pre-flight a transaction (would it revert? honeypot check) before signing anything | `ok`, `returnData` or `revertSelector`, `error` | The simulated outcome at a pinned block |

```bash
A=https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/examples/agent-check/agent_check.py
uv run $A --tool x402_inspect_endpoint --input '{"url":"https://your-api.example/paid"}' --pay --max 10000
uv run $A --tool stock_token_quote --input '{"symbol":"AAPL"}' --pay --max 10000
uv run $A --tool stock_token_halt_status --input '{"symbol":"TSLA"}' --pay --max 10000
uv run $A --tool chain_simulate --input '{"to":"0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168","data":"0x18160ddd"}' --pay --max 10000
```

(`TOLLEX_PRIVATE_KEY` must be set for `--pay`. `0x18160ddd` is `totalSupply()`.) Planning which capability fits a need
is free: `curl -s https://api.tollex.org/v1/resolve -H 'content-type: application/json' -d '{"need":"..."}'`.

## If it does not work

Tell us in [GitHub Discussions](https://github.com/ShiftAboveCtrl/tollex/discussions) or an issue: the HTTP status and
the `error` field are enough. A refused payment (`402` with `invalid_exact_evm_*`) never moves money. Common causes are
in the [troubleshooting table](QUICKSTART.md#troubleshooting).

Listed on [x402scan](https://www.x402scan.com/server/a3852f7b-932a-4983-b93c-27529f112bcd) (35 paid resources).
