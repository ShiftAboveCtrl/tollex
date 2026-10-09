"""python verify_receipt.py [receiptId]   (default: the first mainnet settlement's receipt)"""
import sys

import tollex_client as tollex

rid = sys.argv[1] if len(sys.argv) > 1 else "rcpt_i-xD2HIyq46pjn0z"
v = tollex.verify_receipt(tollex.get_receipt(rid))
print({"receiptId": rid, **v})
sys.exit(0 if v["valid"] else 1)
