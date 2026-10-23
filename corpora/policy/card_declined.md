---
policy_id: "POL-CARD-DECLINE-01"
version: "v1.0"
title: "Point-of-Sale and International Card Decline Resolution Procedure"
intent_labels:
  - "card_declined"
  - "card_not_working"
risk_level: "medium"
owner: "Card Fraud & Risk Operations"
effective_from: "2026-01-01"
effective_to: null
status: "active"
---

# Point-of-Sale and International Card Decline Resolution Procedure

## 1. Overview and Purpose
This operational procedure governs the verification and immediate resolution of card decline events at merchant point-of-sale (POS) terminals, online payment gateways, and foreign automated teller systems. The objective is to restore legitimate purchasing capability while preventing unauthorized card exploitation.

## 2. Customer Identification and Verification (Mandatory Level 3)
Before discussing transaction decline details or modifying card security settings, the customer service specialist must verify identity through one of the following methods:
1. Mobile Push Authentication: Send a real-time prompt to the registered mobile banking app and confirm response code.
2. Two-Factor SMS One-Time Passcode (OTP): Dispatch an ephemeral 6-digit OTP to the phone number on file for at least 30 days.
3. Cardholder Biometric Voiceprint: Automated IVR acoustic match with a confidence score exceeding 0.90.

> **Caution:** If biometric match fails and OTP is delivered to a device changed within 48 hours, escalate immediately to Tier 2 Fraud Investigation.

## 3. Real-Time Authorization Decline Diagnosis
Once identity is confirmed, inspect the Real-Time Authorization Log in the Card Management Console:
1. Decline Reason Code 05 (Do Not Honor / General Decline): Indicates velocity check or rule violation.
2. Decline Reason Code 59 (Suspected Fraud): Geographic or merchant category code (MCC) anomaly triggered automated security hold.
3. Decline Reason Code 62 (Restricted Card): Card temporarily disabled due to inactivity or high-risk location.
4. Decline Reason Code 51 (Insufficient Funds): Account balance or credit limit exceeded.

## 4. Standard Operational Next-Best-Action Procedure
When Decline Reason Code 59 or 62 is identified for a legitimate customer:
1. Step 1: Confirm the merchant name, currency, and exact amount of the declined purchase with the cardholder.
2. Step 2: In the Fraud Management Portal, select the specific transaction and click "Authorize Legitimate Transaction".
3. Step 3: Check the box "Apply 24-Hour Geographic Bypass" for the country or merchant location.
4. Step 4: Advise the customer that the temporary restriction is removed and request that they retry the transaction within 15 minutes.
5. Step 5: If the customer is traveling internationally for multiple days, offer to log a 30-day Travel Notice immediately.

## 5. Escalation and Hard Hold Exceptions
A customer service specialist must NOT lift a card hold if:
1. The card has been flagged for confirmed counterfeit skimming within the last 72 hours.
2. Multiple unauthorized transactions from distinct geographical regions occurred simultaneously.
3. In these scenarios, advise the customer that the card is permanently compromised and initiate expedited replacement delivery.
