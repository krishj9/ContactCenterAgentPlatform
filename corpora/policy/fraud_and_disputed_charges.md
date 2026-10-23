---
policy_id: "POL-FRAUD-DISPUTE-01"
version: "v1.0"
title: "Unauthorized Fraud Investigation and Merchant Billing Dispute Procedure"
intent_labels:
  - "fraud_report"
  - "charged_twice"
  - "Refund_not_showing_up"
risk_level: "high"
owner: "Fraud Investigations & Disputes Management"
effective_from: "2026-01-01"
effective_to: null
status: "active"
---

# Unauthorized Fraud Investigation and Merchant Billing Dispute Procedure

## 1. Overview and Purpose
This procedure defines standard investigation workflows for cardholder fraud claims, duplicate billing charges, and unfulfilled merchant refunds. It ensures compliance with Regulation E (Electronic Fund Transfers) and Regulation Z (Truth in Lending), protecting customers while recovering fraudulent debits through card network dispute channels.

## 2. Customer Identification and Verification (Mandatory Level 3)
Because fraud reporting and dispute filing involve potential account compromise, high-assurance authentication is required:
1. Conduct Mobile In-App Biometric Push or Multi-Factor SMS OTP authentication.
2. Verify customer billing address and last confirmed authorized transaction timestamp and amount.
3. If the cardholder suspects physical theft or credential phishing, treat the session under Compromised Credential Protocol.

## 3. Dispute Eligibility and Regulatory Timelines
1. Unauthorized Fraud Claims (Regulation E / Z): Customer must report unauthorized charges within 60 calendar days of the statement date showing the disputed activity.
2. Duplicate Charges: Occurs when a merchant submits the same authorization reference multiple times. Agent must check authorization IDs and merchant clearing records.
3. Missing Merchant Refunds: If a merchant agreed to a refund and issued a return voucher or credit receipt, customer must allow 15 business days for bank settlement before initiating a formal dispute.
4. Provisional Credit: Provisional credit is mandatory within 10 business days of notice for eligible debit card claims exceeding $50.00 while investigation is underway.

## 4. Standard Operational Next-Best-Action Procedure
When an authenticated customer reports fraudulent charges, duplicate debits, or missing merchant refunds:
1. Step 1: Immediately restrict the compromised card to prevent further unauthorized activity by applying a "Fraud Suspect - Lock" status.
2. Step 2: Review recent cleared and pending transactions with the customer to identify every unauthorized or duplicate item.
3. Step 3: In the Dispute Operations Center, create a new Case Claim:
   - For unauthorized fraud, select claim code "FRAUD-UNAUTHORIZED-CARD-PRESENT-OR-CNP".
   - For duplicate charges, select claim code "BILLING-DUPLICATE-CHARGE" and link both matching transactions.
   - For missing refunds, select claim code "CREDIT-NOT-PROCESSED" and attach merchant cancellation/refund reference.
4. Step 4: Issue provisional credit if eligible under Regulation E guidelines, noting case reference ID.
5. Step 5: Initiate expedited reissue of a new card with a fresh primary account number (PAN) and dispatch an automated dispute confirmation letter to the customer's email.

## 5. Escalation and Law Enforcement Coordination
1. If aggregate fraud exceeds $5,000.00 across multiple accounts, flag the case for Urgent Special Investigations Unit (SIU) review within 2 hours.
2. Provide the customer with the Dispute Case Number for local police report filing if requested.
