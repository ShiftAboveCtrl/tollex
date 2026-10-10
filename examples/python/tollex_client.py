"""Minimal Tollex client: discovery, free planning, payment terms, a guarded x402 payment and receipt
verification, against the public production API. Dependencies: requests, eth-account, rfc8785.

Nothing here spends unless you call buy() with a private key and an explicit ceiling.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import time
from typing import Any

import requests
import rfc8785
from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak, to_checksum_address

TOLLEX = os.environ.get("TOLLEX_URL", "https://api.tollex.org")
TIMEOUT = 30

# The payment rails Tollex accepts. Pinned: a 402 asking for another network, asset, or more than your
# ceiling is refused before anything is signed.
RAILS = {
    "base": {"network": "eip155:8453", "chain_id": 8453, "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "symbol": "USDC", "explorer": "https://base.blockscout.com/tx/"},
    "robinhood": {"network": "eip155:4663", "chain_id": 4663, "asset": "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168", "symbol": "USDG", "explorer": "https://robinhoodchain.blockscout.com/tx/"},
}
# Backwards-compatible names (Robinhood Chain rail).
NETWORK, CHAIN_ID, USDG, BLOCKSCOUT = RAILS["robinhood"]["network"], 4663, RAILS["robinhood"]["asset"], RAILS["robinhood"]["explorer"]


class SpendPolicy:
    """Enforced locally before any signature: per-call ceiling, session budget, allowed rails."""

    def __init__(self, max_per_call: int, max_per_session: int, rails: list[str]):
        self.max_per_call, self.max_per_session, self.rails, self.spent = max_per_call, max_per_session, rails, 0

    def check(self, rail: str, amount: int) -> None:
        if rail not in self.rails:
            raise ValueError(f"rail {rail} not allowed by policy")
        if amount > self.max_per_call:
            raise ValueError(f"refusing to pay {amount} > per-call ceiling {self.max_per_call} (nothing signed)")
        if self.spent + amount > self.max_per_session:
            raise ValueError(f"refusing to pay {amount}: session budget {self.spent}/{self.max_per_session} (nothing signed)")


class Rejected(Exception):
    """The payment was refused before anything was sent on chain; no funds moved."""


def discover() -> dict:
    """1. Service descriptor: network, asset, endpoints, receipt format."""
    return requests.get(f"{TOLLEX}/.well-known/tollex.json", timeout=TIMEOUT).json()


def plan(need: str, input: dict | None = None, max_cost: int | None = None) -> dict:
    """2. Free planning: which capability fits, and what it costs. Never spends."""
    body: dict[str, Any] = {"need": need}
    if input is not None:
        body["input"] = input
    if max_cost is not None:
        body["constraints"] = {"maxCost": str(max_cost)}
    return requests.post(f"{TOLLEX}/v1/resolve", json=body, timeout=TIMEOUT).json()


def _b64json(header: str) -> dict:
    return json.loads(base64.b64decode(header))


def terms(tool_id: str, input: dict, rail: str = "robinhood") -> dict:
    """3. An unpaid call returns HTTP 402 with the exact, authoritative terms (one option per rail)."""
    return terms_for("POST", f"/tools/{tool_id}", input, rail)


def terms_for(method: str, path: str, input: dict | None, rail: str) -> dict:
    r_ = RAILS[rail]
    r = requests.request(method, f"{TOLLEX}{path}", json=input, timeout=TIMEOUT)
    if r.status_code == 503:
        raise RuntimeError("paid calls paused (network gas spike); retry later, nothing was charged")
    if r.status_code != 402:
        raise RuntimeError(f"expected 402 payment terms, got {r.status_code}")
    challenge = _b64json(r.headers["payment-required"])
    for option in challenge["accepts"]:
        if option["network"] == r_["network"] and to_checksum_address(option["asset"]) == to_checksum_address(r_["asset"]):
            return {"method": method, "url": f"{TOLLEX}{path}", "input": input, "rail": rail, "amount": int(option["amount"]), "option": option, "challenge": challenge}
    raise RuntimeError(f"no {r_['symbol']} option on {r_['network']} in the challenge (offered: {[a['network'] for a in challenge['accepts']]})")


def _authorization(account, option: dict, chain_id: int = CHAIN_ID) -> dict:
    """EIP-3009 transferWithAuthorization for exactly the quoted amount, to the quoted recipient."""
    auth = {
        "from": account.address,
        "to": to_checksum_address(option["payTo"]),
        "value": str(option["amount"]),
        "validAfter": "0",
        "validBefore": str(int(time.time()) + int(option["maxTimeoutSeconds"])),
        "nonce": "0x" + secrets.token_hex(32),
    }
    typed = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ],
        },
        "primaryType": "TransferWithAuthorization",
        "domain": {"name": option["extra"]["name"], "version": option["extra"]["version"], "chainId": chain_id, "verifyingContract": to_checksum_address(option["asset"])},
        "message": {**auth, "value": int(auth["value"]), "validAfter": 0, "validBefore": int(auth["validBefore"]), "nonce": bytes.fromhex(auth["nonce"][2:])},
    }
    signed = account.sign_message(encode_typed_data(full_message=typed))
    return {"authorization": auth, "signature": "0x" + signed.signature.hex().removeprefix("0x")}


def buy(private_key: str, tool_id: str, input: dict, max_atomic: int, rail: str = "robinhood", policy: "SpendPolicy | None" = None) -> dict:
    """4. Pay and call a capability on ONE pinned rail, ONLY at or below the ceiling."""
    return pay(private_key, terms(tool_id, input, rail), policy or SpendPolicy(max_atomic, max_atomic, [rail]))


def pay(private_key: str, t: dict, policy: SpendPolicy) -> dict:
    """Sign exactly the quoted amount for the pinned rail and resend; returns the result and the settlement."""
    policy.check(t["rail"], t["amount"])
    account = Account.from_key(private_key)
    payment = {"x402Version": 2, "accepted": t["option"], "resource": t["challenge"]["resource"], "payload": _authorization(account, t["option"], RAILS[t["rail"]]["chain_id"])}
    header = base64.b64encode(json.dumps(payment, separators=(",", ":")).encode()).decode()
    r = requests.request(t["method"], t["url"], json=t["input"], headers={"PAYMENT-SIGNATURE": header}, timeout=120)
    if r.status_code == 402:
        raise Rejected(r.json().get("error", "rejected"))
    settlement = _b64json(r.headers["payment-response"]) if "payment-response" in r.headers else None
    if r.status_code == 200:
        policy.spent += t["amount"]
    tx = (settlement or {}).get("transaction")
    return {"status": r.status_code, "result": r.json(), "settlement": settlement, "explorer": f"{RAILS[t['rail']]['explorer']}{tx}" if tx else None}


def operation(operation_id: str) -> dict:
    """If a response was lost, ask for the operation's state instead of paying again."""
    return requests.get(f"{TOLLEX}/tollex/operations/{operation_id}", timeout=TIMEOUT).json()


def get_receipt(receipt_id: str) -> dict:
    return requests.get(f"{TOLLEX}/tollex/receipts/{receipt_id}", timeout=TIMEOUT).json()


def verify_receipt(receipt: dict) -> dict:
    """5. contentHash = keccak256(RFC 8785 JSON of the body); the EIP-712 signer must be an ACTIVE Tollex key."""
    body = receipt["body"]
    content_hash = "0x" + keccak(rfc8785.dumps(body)).hex()
    typed = {
        "types": {
            "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}],
            "ExecutionReceipt": [
                {"name": "version", "type": "uint256"},
                {"name": "receiptId", "type": "string"},
                {"name": "contentHash", "type": "bytes32"},
                {"name": "issuedAt", "type": "uint256"},
            ],
        },
        "primaryType": "ExecutionReceipt",
        "domain": {"name": "Tollex Execution Receipt", "version": "1"},
        "message": {"version": int(body["version"]), "receiptId": body["receiptId"], "contentHash": bytes.fromhex(content_hash[2:]), "issuedAt": int(body["issuedAt"])},
    }
    signer = Account.recover_message(encode_typed_data(full_message=typed), signature=receipt["signature"])
    keys = requests.get(f"{TOLLEX}/.well-known/tollex-receipt-keys", timeout=TIMEOUT).json()["keys"]
    active = any(k["status"] == "active" and to_checksum_address(k["address"]) == signer for k in keys)
    hash_ok = content_hash == receipt["contentHash"]
    return {"valid": hash_ok and active, "contentHashMatches": hash_ok, "signer": signer, "signerIsActiveTollexKey": active}
