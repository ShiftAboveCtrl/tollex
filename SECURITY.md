# Security

## Reporting a vulnerability

Email **security@tollex.org**. Please include:

- the affected surface (for example `https://api.tollex.org/...`, a discovery document, a receipt);
- what you observed and how to reproduce it;
- the impact you believe it has;
- whether funds, keys or other users could be affected.

Please do not open a public GitHub issue for security reports. We acknowledge reports as quickly as we
can and keep reporters informed until the issue is resolved.

## Scope

In scope: the production service at `https://api.tollex.org`, its discovery documents, x402 payment
handling, receipts and the published receipt keys.

Out of scope: denial-of-service or load testing, social engineering, physical attacks, and third-party
services (Robinhood Chain, RPC providers, Cloudflare, external x402 merchants).

## Rules for testing

- Use only your own wallets and funds. Never attempt to move funds you do not own.
- Do not run automated scanners or high-volume traffic against production; rate limits apply.
- Do not access, modify or retain data that is not yours.
- Stop and report as soon as you have shown the issue.

We will not pursue legal action against good-faith research that follows these rules.

## Published keys and addresses

The only keys and addresses that speak for Tollex are those listed in
[evidence/mainnet-launch.public.json](evidence/mainnet-launch.public.json) and the live receipt key set
at `https://api.tollex.org/.well-known/tollex-receipt-keys`. Treat anything else claiming to be Tollex
with suspicion and report it.
