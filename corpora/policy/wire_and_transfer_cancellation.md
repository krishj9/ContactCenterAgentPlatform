---
policy_id: "POL-TRANSFER-CANCEL-01"
version: "v1.0"
title: "Domestic and International Funds Transfer Cancellation Procedure"
intent_labels:
  - "cancel_transfer"
risk_level: "high"
owner: "Payment Operations & Treasury Clearing"
effective_from: "2026-01-01"
effective_to: null
status: "active"
---

# Domestic and International Funds Transfer Cancellation Procedure

## 1. Overview and Purpose
This policy governs the cancellation, recall, and stop-payment workflows for scheduled, pending, and transmitted electronic fund transfers, including ACH payments, domestic Fedwire, and international SWIFT wire transfers.

## 2. Customer Identification and Verification (Mandatory Level 3)
Because transfer cancellation touches active capital movements, Level 3 authentication is enforced:
1. Conduct Mobile Push Biometric confirmation or SMS OTP.
2. Verify originating account number, recipient name, transfer amount, and date initiated.

## 3. Transfer Cancellation Windows and Network Limitations
1. Scheduled Future-Dated Transfers (ACH & Internal): Can be canceled anytime prior to 8:00 PM Eastern Time on the business day prior to the scheduled execution date with 100% success guarantee and zero fee.
2. Same-Day ACH Transfers: Can be canceled only if the payment is in "Pending Batch" status. Once the batch is submitted to the clearinghouse (cutoffs: 10:30 AM, 2:45 PM, 4:45 PM ET), direct cancellation is impossible; an ACH Return Request (R06 - Returned per ODFI Request) must be filed.
3. Wire Transfers (Fedwire / SWIFT): Once wire status is "Released to Network", the transfer cannot be canceled unilaterally. A "Recall of Funds Request" (SWIFT MT192 / MT292 or Fedwire Service Message) must be transmitted to the beneficiary bank. Recovery depends entirely on beneficiary bank and recipient consent.

## 4. Standard Operational Next-Best-Action Procedure
When an authenticated customer requests to cancel or recall a funds transfer:
1. Step 1: Open the Funds Transfer Operations Console and locate the transaction reference number.
2. Step 2: Check the exact status of the transfer:
   - If "Scheduled" or "Queued - Unreleased": Click "Cancel Transfer" immediately. Confirm cancellation to customer and release held funds back to available balance.
   - If "Released to Clearinghouse / Settled": Advise customer that funds have departed and initiate a formal Recall Request.
3. Step 3: For wires already released, submit an urgent "Wire Recall Order" through the SWIFT/Fedwire gateway with reason "Customer Requested Recall / Suspected Misdirection".
4. Step 4: Disclose recall processing fees ($25.00 for domestic Fedwire recall, $40.00 for SWIFT recall) and inform customer that recovery timeline ranges from 2 to 10 business days.
5. Step 5: Issue a Recall Reference Number to the customer and log an automated follow-up notification in the ticketing system.

## 5. Escalation for Scam and Authorized Push Payment (APP) Fraud
1. If the transfer was induced by a social engineering scam, executive impersonation, or crypto extortion scheme, immediately notify the Anti-Money Laundering (AML) / Urgent Fraud Intercept Desk to send a priority recall freeze request to the recipient institution.
