/** npm run verify-receipt -- <receiptId>   (default: the first mainnet settlement's receipt) */
import { getReceipt, verifyReceipt } from "./tollex.js";

const id = process.argv[2] ?? "rcpt_i-xD2HIyq46pjn0z";
const receipt = await getReceipt(id);
const v = await verifyReceipt(receipt);
console.log({ receiptId: id, ...v, settlement: receipt.body.settlement });
if (!v.valid) process.exit(1);
