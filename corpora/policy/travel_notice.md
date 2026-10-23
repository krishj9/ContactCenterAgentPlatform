---
policy_id: "POL-TRAVEL-NOTICE-01"
version: "v1.0"
title: "Customer Travel Notice Registration and Foreign Transaction Exemption Procedure"
intent_labels:
  - "travel_notice"
risk_level: "low"
owner: "Fraud Operations & Travel Security"
effective_from: "2026-01-01"
effective_to: null
status: "active"
---

# Customer Travel Notice Registration and Foreign Transaction Exemption Procedure

## 1. Overview and Purpose
This standard operating policy outlines the steps required to log domestic or international travel itineraries on customer debit and credit cards. Registering travel prevents automated fraud detection systems from triggering false-positive transaction declines while the cardholder is traveling outside their primary metropolitan area or home country.

## 2. Customer Identification and Verification
Prior to recording travel plans or altering risk parameters, the customer service specialist must verify cardholder identity using Standard Level 2 verification:
1. Confirm customer full name, billing address, and date of birth.
2. Authenticate through One-Time Passcode (OTP) sent to the verified mobile device, or via in-app Push Notification confirmation.
3. Validate the last 4 digits of the payment card(s) to be placed on travel notice.

## 3. Policy Rules and Constraints
1. Travel notices may be registered up to 90 calendar days in advance of the planned departure date.
2. The maximum single continuous travel notice window is 60 calendar days. Itineraries exceeding 60 days require supervisory review or periodic extension checkpoints.
3. Up to 10 destination countries or transit territories may be linked to a single notice record.
4. Embargoed and sanctioned jurisdictions (OFAC high-risk destinations) cannot be enabled for card transactions under any circumstances. If requested, inform the customer immediately that bank cards cannot operate in these regions.

## 4. Standard Operational Next-Best-Action Procedure
When an authenticated customer requests a travel notice registration:
1. Step 1: Capture departure date, return date, and all destination countries/states.
2. Step 2: Open the Card Security Console and navigate to the "Travel & Geographic Exemptions" tab.
3. Step 3: Enter the travel dates and select destination country codes. Ensure all active primary and secondary cards requested by the customer are selected.
4. Step 4: Click "Register Travel Profile" and verify that the confirmation banner displays "Exemption Rules Active".
5. Step 5: Inform the customer of foreign exchange transaction fee rates (0% for Premium, 3% for Standard tiers) and advise them to save the 24/7 International Collect Assistance phone number.

## 5. Exceptions and Troubleshooting
1. If the customer is already abroad and reporting declined transactions, execute Step 1 through Step 4, then submit a real-time "Clear Cached Risk Profile" override. The override activates within 5 minutes.
2. If the customer reports lost luggage containing secondary cards, do not register travel for those cards; place an immediate temporary freeze on them.
