# Mainnet launch (2026-10-08)

![First Tollex mainnet settlement](../assets/launch-proof.svg)

Tollex was enabled for payments on Robinhood Chain mainnet on 2026-10-08 with a single command that
refused to proceed unless every check passed, and that would have returned production to read-only
on any failure.

## Sequence

1. **Read-only production.** The service ran on mainnet with discovery, planning and correct 402
   challenges, while every payment was refused.
2. **Preflight.** Every gate passed: clean source tree with green CI, adopted economic policy,
   external mainnet execution disabled, signing keys live at their pinned addresses, receipt signer
   unfunded, relayer balance within bounds, gas and spending envelopes, contract code hashes on two
   independent RPC providers, chain capability probe, database TLS and a restore drill, alert delivery,
   production readiness and public discovery.
3. **Release.** A release manifest was built for source commit `abff565c2188` and image
   `sha256:ba35243f137d7c3dfdd053957bb80cf40df8f26a37210670856d5c5ef57678ae`
   (subject hash `b5dfdce5c677aaab812b7edbad0de881d253aa8e93b2377ea16eb24b1d63caa9`), signed by the owner
   and verified.
4. **Writes enabled with one canary.** A single 0.001 USDG payment was made through the full public
   payment path, from the operator's test payer to the treasury.
5. **On-chain verification.** All checks below were read back from the chain and recorded.
6. **Canary stopped; postflight discovery passed.** Production stayed in launch mode.

## The first settlement

| Field | Value |
| --- | --- |
| Transaction | [`0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533`](https://robinhoodchain.blockscout.com/tx/0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533) |
| Explorer | [View on Blockscout](https://robinhoodchain.blockscout.com/tx/0x82f1c72cdc3d27bcb7dac1391222fd6e5462ec3c91352c82e2ff0801eda1c533) |
| Block | 83335219 |
| Method | USDG `transferWithAuthorization` (EIP-3009), sent by the relayer |
| Transfer | 1000 atomic USDG (0.001), canary payer to treasury |
| Gas used | 102950 |
| Gas cost | 102047746200000 wei (cap 800000000000000 wei) |

| Check | Result |
| --- | --- |
| Transaction succeeded | true |
| Sent by the relayer | true |
| Exactly one transfer, payer to treasury, of the quoted amount | true |
| Payer charged the quoted amount | true |
| Treasury credited the quoted amount | true |
| Relayer paid gas only | true |
| Gas within the launch envelope | true |
| Receipt signer untouched | true |
| Authorization recorded as used (no replay possible) | true |
| Receipt verified by the canary | true |
| Settlement reconciled by the canary | true |

Machine-readable record: [evidence/mainnet-launch.public.json](../evidence/mainnet-launch.public.json).
Checksums: [evidence/checksums.txt](../evidence/checksums.txt). How to check it: [VERIFY.md](VERIFY.md).

## After launch

- The scheduled canary was stopped; Tollex does not make test payments on a schedule.
- External third-party mainnet routing remains disabled.
- The source commit identifies a private revision; later documentation commits do not change what
  was deployed.
