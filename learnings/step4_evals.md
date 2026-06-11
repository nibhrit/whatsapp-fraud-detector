# Step 4: Evals

## What we built

Two files:

| File | Purpose |
|------|---------|
| `evals/test_messages.json` | 30 labelled test messages — ground truth for measuring the system |
| `evals/evals.py` | Script that runs all 30 through the live API and prints a metrics report |

---

## The test set design

30 messages: **15 fraud, 15 legitimate**.

**Fraud messages** cover all 5 categories (3 per category):
- UPI / KYC Fraud — English, Hindi, Hinglish, English
- Fake Job Offers — English, Hinglish, English, English
- Lottery / Prize Scams — Hinglish, English, Hindi
- Bank Impersonation — English, Hinglish, Hindi
- Investment Fraud — English

**Legitimate messages** cover 3 types (5 per type):
- Casual / Personal — friend making plans, birthday message, family update
- Service / Transactional — OTP, Uber, Zomato, Amazon, IRCTC
- Professional / Reminder — clinic appointment, work meeting, refund confirmation

**Language distribution:**
- English: 13 messages
- Hinglish: 10 messages
- Hindi: 7 messages

### The tricky cases (by design)

Two legitimate messages were chosen specifically to test the false positive risk:

1. **PhonePe OTP** (`legit_06`) — contains a code and "Do not share" phrasing, which overlaps with fraud message patterns. The system correctly passed it as legitimate.
2. **BESCOM electricity bill reminder** (`legit_15`) — mentions electricity bill and payment, which overlaps with our "Electricity Bill Cutoff Threat" fraud pattern. The system correctly passed it as legitimate because the tone is a reminder, not a threat, and points to an official app.

---

## Results

```
Accuracy           : 100%
Precision          : 100%
Recall             : 100%
False Positive Rate: 0%    ← primary metric

True  Positives : 15  (fraud caught)
False Negatives : 0   (fraud missed)
True  Negatives : 15  (legit passed correctly)
False Positives : 0   (legit wrongly flagged)
```

---

## What the metrics mean

**Precision** — of all messages the system labelled FRAUD, what fraction were actually fraud?
- 100% means: every single thing it flagged was genuinely suspicious. No crying wolf.

**Recall** — of all the actual fraud messages, what fraction did the system catch?
- 100% means: nothing slipped through.

**False Positive Rate (FPR)** — of all legitimate messages, what fraction did the system wrongly flag as fraud?
- 0% means: not a single real message was flagged incorrectly.
- This is the primary metric because a high FPR destroys user trust. If your messages to family get flagged as fraud, you stop using the tool.

---

## How the evals script works

1. Pings `/health` first — exits with a clear error if the server isn't running
2. Loops through all 30 cases, calls `POST /analyse` for each
3. Compares `expected` vs `got` (the verdict from the API)
4. Calculates TP, FP, TN, FN and derives metrics
5. Prints a full results table and highlights any failures

The 0.5 second delay between calls (`time.sleep(0.5)`) is deliberate — prevents hammering the API and is closer to realistic usage patterns.

---

## Important caveat for interviews

100% on a 30-message test set is a strong result but should be presented honestly:

- The test set was written by the same person who built the system — there is no independent test set
- 30 messages is a small sample; a production system would need thousands
- Real-world fraud messages are more varied, use more obfuscation (misspellings, symbols), and evolve constantly

The honest interview framing: *"On a 30-message internal test set, the system achieved 100% accuracy and 0% false positive rate. The next step would be testing against a blind set of real-world messages and iterating on prompt and pattern library based on failures."*

---

## How to run

```bash
# Terminal 1 — start the server
cd backend
python3 -m uvicorn main:app

# Terminal 2 — run evals (from project root)
python3 evals/evals.py
```
