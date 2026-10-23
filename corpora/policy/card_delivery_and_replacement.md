---
policy_id: "POL-CARD-DELIVERY-01"
version: "v1.0"
title: "Physical Card Order, Delivery Tracking, and Activation Procedure"
intent_labels:
  - "card_arrival"
  - "order_physical_card"
risk_level: "low"
owner: "Card Fulfillment & Retail Operations"
effective_from: "2026-01-01"
effective_to: null
status: "active"
---

# Physical Card Order, Delivery Tracking, and Activation Procedure

## 1. Overview and Purpose
This policy governs standard and expedited fulfillment of physical debit, credit, and prepaid cards, tracking postal shipments, addressing non-delivery inquiries, and guiding customers through card activation and PIN creation.

## 2. Customer Identification and Verification
Standard Level 2 customer authentication is required before sharing dispatch details or initiating re-orders:
1. Confirm customer name, primary billing address, and phone number.
2. Verify via SMS OTP or interactive mobile banking push notification.

## 3. Delivery Service Level Agreements (SLAs) and Rules
1. Standard First-Class Delivery: Dispatched within 24 hours of ordering; expected delivery within 5 to 7 business days (US domestic) or 10 to 14 business days (international).
2. Expedited Courier Delivery: Dispatched via priority carrier (FedEx / UPS) within 1 business day; delivered in 1 to 2 business days. Free for Premier tier, $15.00 fee for Standard tier.
3. Non-Arrival Threshold: If a card has not arrived after 10 business days from dispatch date, it is deemed lost in transit. The original card must be voided and a replacement reissued.
4. Security Invariant: Replacement cards must only be sent to the primary address on file unless the customer has maintained an updated secondary address for at least 30 days.

## 4. Standard Operational Next-Best-Action Procedure
When an authenticated customer inquires about card arrival or requests a new physical card:
1. Step 1: Open the Card Logistics Console and look up the customer's pending or dispatched card orders.
2. Step 2: Check the carrier tracking number and status:
   - If status is "In Transit" and within the 7 business day window, provide carrier tracking details and estimated arrival date.
   - If order is older than 10 business days and tracking is stalled, void the original card token ("Void - Transit Loss").
3. Step 3: If customer needs a new or replacement card, verify mailing address and card design preferences.
4. Step 4: Submit the card order, choosing standard delivery (default) or expedited courier if urgent travel or business needs require it.
5. Step 5: Instruct the customer on how to activate the card upon arrival via mobile app, online banking, or IVR toll-free line (1-800-555-CARD).

## 5. Escalation and Special Scenarios
1. If the card was returned to the sender (RTS) due to incorrect postal address, confirm the updated address, obtain supervisory validation if changed recently, and reissue.
2. Never provide unmasked full card numbers over the telephone or chat interface under any circumstances.
