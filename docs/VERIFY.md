# Verify Tollex independently

You need `curl` and `jq`. Nothing here pays, signs or writes.

## One command

```bash
scripts/verify-live.sh --chain
```

Each line is `PASS`, `WARN` or `FAIL`. `WARN` on the x402 check means paid calls are paused because
settlement gas rose sharply (a deliberate, fail-closed state; nothing is charged).

## By hand

### 1. The service is up and on the right network

```bash
curl -s https://api.tollex.org/ready
curl -s https://api.tollex.org/.well-known/tollex.json | jq '{name, networks: .payment.networks, assets: .payment.assets}'
```

Expect `{"ready":true}`, network `eip155:4663` and USDG `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`.

### 2. The receipt key is the published receipt signer

```bash
curl -s https://api.tollex.org/.well-known/tollex-receipt-keys | jq '.keys[] | {address, status}'
```

Expect `0x69d778C105b7f94Bde775d7ae94F1daa56DAA88F`, `active`.

### 3. Payment terms

See [X402.md](X402.md) to decode a live 402 challenge. Expect network `eip155:4663`, asset USDG and
`payTo` `0x2eB98e76db13287eD4AEE5F1C7f14a7e378966B7`.

### 4. The launch settlement on chain

Any Robinhood Chain mainnet RPC works; the public one is used here.

```bash
RPC=https://rpc.mainnet.chain.robinhood.com
TX=0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533
curl -s $RPC -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' | jq -r .result        # 0x1237 = 4663
curl -s $RPC -H 'content-type: application/json' \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$TX\"]}" \
  | jq '.result | {status, blockNumber, from, to, gasUsed, logs: [.logs[] | {address, topics, data}]}'
```

Expect:

- `status` `0x1`, `blockNumber` `0x4f79833` (83335219), `gasUsed` `0x19226` (102950);
- `from` the relayer `0xcbe1b48c188edf24b3c939e46647a80fb9f75645`, `to` the USDG contract;
- a `Transfer` log (topic `0xddf252ad...`) from the canary payer `0x488bf185...4841` to the treasury
  `0x2eb98e76...66b7` with data `0x...03e8` (1000);
- an `AuthorizationUsed` log (topic `0x98de5035...`), which makes the authorization unusable again.

The transaction input starts with `0xe3ee160e`, the selector of
`transferWithAuthorization(address,address,uint256,uint256,uint256,bytes32,uint8,bytes32,bytes32)`.

### 5. The receipt signer holds nothing

```bash
curl -s $RPC -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":["0x69d778C105b7f94Bde775d7ae94F1daa56DAA88F","latest"]}' | jq -r .result
```

Expect `0x0`.

## Integrity of the evidence file

```bash
shasum -a 256 evidence/mainnet-launch.public.json   # compare with evidence/checksums.txt
```
