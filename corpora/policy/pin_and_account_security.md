---
policy_id: "POL-PIN-SECURITY-01"
version: "v1.0"
title: "Card PIN Lockout, Unblock, and Credential Reset Policy"
intent_labels:
  - "pin_blocked"
risk_level: "medium"
owner: "Security Architecture & Retail Authentication"
effective_from: "2026-01-01"
effective_to: null
status: "active"
---

# Card PIN Lockout, Unblock, and Credential Reset Policy

## 1. Overview and Purpose
This policy establishes security controls for handling debit and credit card Personal Identification Number (PIN) lockout events resulting from repeated incorrect entries at automated teller machines (ATMs) or merchant point-of-sale chip terminals.

## 2. Customer Identification and Verification (Mandatory Level 3)
Because PIN manipulation allows direct cash extraction at ATMs, strict Level 3 authentication is mandatory:
1. Conduct Mobile Banking In-App Push Biometric Authentication.
2. If mobile app is unavailable, require SMS OTP to a phone number on file for >= 30 days plus verification of two recent non-PIN transactions and government ID number.
3. If suspicious account changes occurred in the last 72 hours, do not unblock PIN over phone; require in-branch visit with physical photo ID.

## 3. Policy Rules and Lockout Controls
1. Retry Threshold: A payment card is automatically locked after three (3) consecutive incorrect PIN attempts at an ATM or chip terminal.
2. Chip Lockout Behavior: PIN retry counters are stored directly on the physical EMV chip. Unblocking the counter in the core system resets server-side authorization, but the chip counter itself synchronizes only when inserted into a compatible online ATM.
3. Absolute Restriction: Customer service agents must NEVER ask for, record, view, or enter a customer's PIN. All PIN selection must be performed by the customer via secure IVR keypad or mobile app.

## 4. Standard Operational Next-Best-Action Procedure
When an authenticated customer experiences a PIN block:
1. Step 1: Open the Card Security Console and navigate to "PIN Management".
2. Step 2: Confirm the lockout reason (e.g., "Counter Reached Maximum Tries = 3").
3. Step 3: Click "Reset PIN Retry Counter" in the core banking system to remove the server-side block.
4. Step 4: Transfer the customer to the Automated Secure PIN IVR or guide them to the "Set/Change Card PIN" screen in the Mobile Banking App to define a new secure PIN.
5. Step 5: Instruct the customer that their first transaction with the new PIN or unlocked chip must be performed at an online bank ATM (by performing a Balance Inquiry or Withdrawal) to refresh the physical EMV chip counter.

## 6. Escalations and Fraud Triggers
1. If PIN lockouts occur across multiple cards owned by the customer simultaneously, escalate to Fraud Investigation immediately and place a temporary hold on outward electronic transfers.
