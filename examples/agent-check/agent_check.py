# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31", "eth-account>=0.13", "rfc8785>=0.1.4"]
# ///
"""Try a real mainnet call: buy GET https://api.tollex.org/v1/agent-check (about 0.008 USD) and verify the receipt.
Add --tool <id> --input '<json>' to buy a capability the same way (e.g. --tool stock_token_quote --input '{"symbol":"AAPL"}').

One command, nothing to clone (uv reads the dependencies above):

    uv run https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/examples/agent-check/agent_check.py
    TOLLEX_PRIVATE_KEY=0x... uv run https://raw.githubusercontent.com/ShiftAboveCtrl/tollex/main/examples/agent-check/agent_check.py --pay --max 10000

Without --pay it only shows the price on each rail. With --pay it signs ONE EIP-3009 authorization for exactly the
quoted amount, never above --max (atomic units, 6 decimals; 10000 = 0.01 USD), on the pinned rail:
  --rail base       USDC on Base (eip155:8453), the default
  --rail robinhood  USDG on Robinhood Chain (eip155:4663)
The key never leaves this process; it is read from TOLLEX_PRIVATE_KEY, never from arguments.
"""
import argparse
import base64
import json
import os
import secrets
import sys
import time

import requests
import rfc8785
from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak, to_checksum_address

API = os.environ.get("TOLLEX_URL", "https://api.tollex.org")
RAILS = {
    "base": {"network": "eip155:8453", "chain_id": 8453, "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "symbol": "USDC", "explorer": "https://base.blockscout.com/tx/"},
    "robinhood": {"network": "eip155:4663", "chain_id": 4663, "asset": "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168", "symbol": "USDG", "explorer": "https://robinhoodchain.blockscout.com/tx/"},
}

p = argparse.ArgumentParser(description="Tollex first paid call")
p.add_argument("--rail", default="base", choices=sorted(RAILS))
p.add_argument("--pay", action="store_true")
p.add_argument("--max", type=int, default=0, help="per-call ceiling in atomic units (required with --pay)")
p.add_argument("--tool", help="buy a capability instead, e.g. stock_token_quote (POST /tools/<id>)")
p.add_argument("--input", default="{}", help="JSON input for --tool, e.g. '{\"symbol\": \"AAPL\"}'")
a = p.parse_args()
method, path, body = ("POST", f"/tools/{a.tool}", json.loads(a.input)) if a.tool else ("GET", "/v1/agent-check", None)
rail = RAILS[a.rail]
b64 = lambda h: json.loads(base64.b64decode(h))

r = requests.request(method, f"{API}{path}", json=body, timeout=30)
if r.status_code != 402:
    sys.exit(f"expected a 402 with payment terms, got HTTP {r.status_code}")
challenge = b64(r.headers["payment-required"])
for o in challenge["accepts"]:
    sym = next((x["symbol"] for x in RAILS.values() if x["network"] == o["network"]), "?")
    print(f"  {o['network']}: {o['amount']} atomic {sym} ({int(o['amount']) / 1e6} USD) to {o['payTo']}")
opt = next((o for o in challenge["accepts"] if o["network"] == rail["network"] and to_checksum_address(o["asset"]) == to_checksum_address(rail["asset"])), None)
if not opt:
    sys.exit(f"no {rail['symbol']} option on {rail['network']} in the challenge; nothing signed")
if not a.pay:
    sys.exit(f"price on {a.rail}: {opt['amount']} atomic {rail['symbol']}. Add --pay --max <atomic units> with TOLLEX_PRIVATE_KEY to buy.")
if int(opt["amount"]) > a.max:
    sys.exit(f"refused locally: price {opt['amount']} is above --max {a.max}; nothing signed")

acct = Account.from_key(os.environ["TOLLEX_PRIVATE_KEY"])
auth = {"from": acct.address, "to": to_checksum_address(opt["payTo"]), "value": str(opt["amount"]), "validAfter": "0", "validBefore": str(int(time.time()) + int(opt["maxTimeoutSeconds"])), "nonce": "0x" + secrets.token_hex(32)}
typed = {
    "types": {
        "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}, {"name": "chainId", "type": "uint256"}, {"name": "verifyingContract", "type": "address"}],
        "TransferWithAuthorization": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "validAfter", "type": "uint256"}, {"name": "validBefore", "type": "uint256"}, {"name": "nonce", "type": "bytes32"}],
    },
    "primaryType": "TransferWithAuthorization",
    "domain": {"name": opt["extra"]["name"], "version": opt["extra"]["version"], "chainId": rail["chain_id"], "verifyingContract": to_checksum_address(opt["asset"])},
    "message": {**auth, "value": int(auth["value"]), "validAfter": 0, "validBefore": int(auth["validBefore"]), "nonce": bytes.fromhex(auth["nonce"][2:])},
}
sig = "0x" + acct.sign_message(encode_typed_data(full_message=typed)).signature.hex().removeprefix("0x")
header = base64.b64encode(json.dumps({"x402Version": 2, "accepted": opt, "resource": challenge["resource"], "payload": {"authorization": auth, "signature": sig}}, separators=(",", ":")).encode()).decode()
r = requests.request(method, f"{API}{path}", json=body, headers={"PAYMENT-SIGNATURE": header}, timeout=120)
if r.status_code == 402:
    sys.exit(f"rejected before anything was sent on chain (nothing moved): {r.json().get('error')}")
if r.status_code == 202:
    sys.exit(f"settlement pending: resend the SAME request later or check {r.json().get('operationId')}; do not sign again")
settle = b64(r.headers["payment-response"])
print(f"\npaid on {rail['network']}: {rail['explorer']}{settle.get('transaction')}")
print(json.dumps(r.json(), indent=2))

receipt = (settle.get("extensions") or {}).get("tollex-receipt", {}).get("info")
if receipt:
    content_hash = "0x" + keccak(rfc8785.dumps(receipt["body"])).hex()
    rt = {"types": {"EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}], "ExecutionReceipt": [{"name": "version", "type": "uint256"}, {"name": "receiptId", "type": "string"}, {"name": "contentHash", "type": "bytes32"}, {"name": "issuedAt", "type": "uint256"}]},
          "primaryType": "ExecutionReceipt", "domain": {"name": "Tollex Execution Receipt", "version": "1"},
          "message": {"version": int(receipt["body"]["version"]), "receiptId": receipt["body"]["receiptId"], "contentHash": bytes.fromhex(content_hash[2:]), "issuedAt": int(receipt["body"]["issuedAt"])}}
    signer = Account.recover_message(encode_typed_data(full_message=rt), signature=receipt["signature"])
    keys = requests.get(f"{API}/.well-known/tollex-receipt-keys", timeout=30).json()["keys"]
    active = any(k["status"] == "active" and to_checksum_address(k["address"]) == signer for k in keys)
    print(f"\nreceipt {receipt['body']['receiptId']}: valid={content_hash == receipt['contentHash'] and active} (content hash matches: {content_hash == receipt['contentHash']}, signer {signer} active: {active})")
    print("your operation now appears (privacy-safe reference) on https://tollex.org/activity/")
