---
policy_id: "POL-CARD-SECURITY-01"
version: "v1.0"
title: "Lost, Stolen, and Compromised Payment Card Handling Procedure"
intent_labels:
  - "lost_or_stolen_card"
  - "compromised_card"
risk_level: "high"
owner: "Card Risk & Security Operations"
effective_from: "2026-01-01"
effective_to: null
status: "active"
---

# Lost, Stolen, and Compromised Payment Card Handling Procedure

## 1. Overview and Purpose
This standard operating policy specifies emergency response workflows for physical card theft, loss in transit, or data compromise (such as merchant database breaches or ATM skimming). Prompt card deactivation and token invalidation are critical to mitigating financial loss for both customer and bank.

## 2. Customer Identification and Verification (Mandatory Level 3)
1. Verify customer identity using Out-of-Band (OOB) authentication (Mobile Push or SMS OTP).
2. If phone is also reported lost/stolen with the card, execute Secondary Out-of-Wallet Identity Verification:
   - Verify Date of Birth, Full Social Security Number / National ID.
   - Verify two past account transactions (dates and exact dollar values).
   - Verify registered residential address.

## 3. Policy Rules and Security Controls
1. Immediate Card Invalidation: Once reported lost or stolen, the card token and PAN must be permanently canceled ("Status: HOTCARD - LOST/STOLEN"). A canceled card cannot be reactivated under any circumstance.
2. Digital Wallet Suspension: All linked Apple Pay, Google Wallet, and Samsung Pay digital device tokens must be terminated immediately.
3. Liability Protections: Reassure the cardholder of Zero Liability protection for unauthorized transactions reported within 48 hours of discovering loss.

## 4. Standard Operational Next-Best-Action Procedure
When an authenticated customer reports a lost, stolen, or compromised card:
1. Step 1: Open the Card Security Console and immediately execute "Permanent Block - Hotcard".
2. Step 2: Invalidate all associated mobile wallet tokens and merchant recurring token agreements.
3. Step 3: Conduct a rapid transaction audit of the preceding 7 days with the customer to identify any suspicious transactions requiring dispute filing.
4. Step 4: Click "Reissue Replacement Card" and verify the delivery address on record. If the customer requests delivery to a temporary address, verify that the address change passes secondary risk verification.
5. Step 5: Offer Instant Digital Card Activation so the customer can link the new card to their mobile wallet immediately while waiting for the physical plastic.

## 5. Escalations and Emergency Cash Assistance
1. If the cardholder is stranded without access to funds or payment methods, initiate Western Union or Branch Emergency Cash Wire up to $500.00 upon identity verification.
2. For private wealth and high-net-worth clients, dispatch next-day courier delivery at no charge.
