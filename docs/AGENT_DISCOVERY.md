# Agent discovery

Agents can find out what Tollex offers, what it costs and how to pay without any human setup. Every
surface is public, unauthenticated and free.

| Surface | URL | Purpose |
| --- | --- | --- |
| Descriptor | `https://api.tollex.org/.well-known/tollex.json` | canonical entry point: network, asset, endpoints, receipt format |
| OpenAPI 3.1 | `https://api.tollex.org/openapi.json` | every HTTP operation with schemas |
| llms.txt | `https://api.tollex.org/llms.txt` | concise text guide for language-model agents |
| Catalogue | `https://api.tollex.org/v1/catalog` | every capability with input schema and pricing |
| A2A agent card | `https://api.tollex.org/.well-known/agent-card.json` | skills for agent-to-agent clients |
| A2A endpoint | `https://api.tollex.org/a2a` | JSON-RPC; planning is free |
| Receipt keys | `https://api.tollex.org/.well-known/tollex-receipt-keys` | active receipt-signing keys |
| x402 challenge | any paid capability, unpaid | exact payment terms plus Bazaar metadata |

## Recommended flow for an agent

1. Read the descriptor; confirm the network is `eip155:4663` and the asset is USDG.
2. Ask `POST /v1/resolve` (or the A2A skill `tollex.resolve_intent`) for the capability that fits the
   task and its price. This never spends.
3. Call the capability; read the 402 challenge; check it against the agent's own spending policy.
4. Sign the authorization and retry; keep the receipt.
5. Verify the receipt against the published key set.

## A2A example (free planning)

```bash
curl -s -X POST https://api.tollex.org/a2a \
  -H 'content-type: application/json' -H 'a2a-version: 1.0' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"role":"ROLE_USER","messageId":"example-1","parts":[{"data":{"skill":"tollex.resolve_intent","need":"latest block header on Robinhood Chain"}}]}}}' \
  | jq '.result.task.status.state'
```

## MCP

An MCP endpoint is not advertised in production at this time. Discovery reports exactly what is
served, and `/.well-known/mcp/server-card.json` returns 404 until it is.
