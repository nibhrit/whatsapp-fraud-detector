# Step 2: RAG Pipeline

## What we built

`backend/rag_pipeline.py` — the core intelligence layer. It connects the retrieval from Step 1 (ChromaDB) to the Claude LLM to produce a structured verdict.

---

## What it does, step by step

When `analyse(message)` is called:

1. **Retrieve** — calls `retrieve_patterns(message, n_results=3)` from Step 1. Gets the 3 fraud patterns most semantically similar to the incoming message.
2. **Build prompt** — formats those 3 patterns + the message into a structured user message for Claude.
3. **Call Claude** — sends the system prompt + user message to Claude Haiku and gets a response.
4. **Parse** — strips any markdown fences Claude may have added, then parses the JSON response.
5. **Return** — returns a Python dict with verdict, confidence, pattern, explanation, recommendation, language.

---

## The two-part prompt structure

Every Claude API call has two parts:

**System prompt** — set once, defines Claude's permanent role and rules. Ours tells Claude:
- You are a fraud detection expert for Indian WhatsApp scams
- Be conservative — false positives are worse than misses
- Respond only in JSON, no markdown
- Match the language of the input message in your output

**User message** — changes per request. Contains the 3 retrieved patterns as context, then the message to analyse. This is the RAG injection: we are giving Claude relevant knowledge at call time, not retraining it.

### Why separate these?

The system prompt gets **cached** by the Claude API. After the first call, you only pay input tokens for the user message — not the system prompt again. Small saving at this scale, meaningful at production scale.

---

## Key concept: why RAG beats "just ask Claude"

Without RAG, you would send just the message and ask Claude "is this fraud?" Claude would use its general training knowledge — which is broad but not specific to Indian fraud patterns.

With RAG, you send the message AND the 3 most relevant fraud patterns from your own library. Claude now reasons against specific, curated knowledge. When a new fraud type emerges (e.g., a new scam variant targeting UPI), you add it to your pattern library — Claude's behaviour updates immediately without any retraining or model changes.

This is the PM argument: **the system gets smarter by adding data, not by rebuilding the model.**

---

## Test results (8 messages)

| Message | Expected | Got | Confidence | Language |
|---------|----------|-----|-----------|---------|
| UPI reward Rs 50,000 link | FRAUD | FRAUD | 95% | Hindi |
| Bijli connection kat jayega | FRAUD | FRAUD | 92% | Hindi |
| Amazon HR WFH Rs 500 fee | FRAUD | FRAUD | 92% | English |
| KBC Rs 25 lakh pay fee | FRAUD | FRAUD | 98% | Hindi |
| Dinner at 8? | LEGIT | LEGIT | 99% | English |
| Cricket dekhne chalein? | LEGIT | LEGIT | 98% | Hinglish |
| Swiggy OTP 847291 | LEGIT | LEGIT | 95% | English |
| Mom, home by 7 | LEGIT | LEGIT | 99% | English |

**False positive rate: 0/4 (0%)**
**Fraud recall: 4/4 (100%)**

The Swiggy OTP case is the most important legitimate message. OTP messages can look suspicious (they contain a code and urgency). Claude correctly identified it as a legitimate service message because the phrasing matches known OTP format, not fraud patterns.

---

## Bugs found and fixed

**Bug 1: JSON wrapped in markdown fences**
Claude returned ` ```json { ... } ``` ` instead of raw JSON, even though the prompt said not to. Fixed with a `_strip_fences()` helper that removes the fences before parsing. This is a common LLM behaviour — always defensive-parse LLM output.

**Bug 2: max_tokens too low**
Set initially to 512 — Claude's detailed explanations in Hindi/Hinglish exceeded this and the JSON got truncated mid-string. Raised to 1024.

---

## Product decision: conservative bias

The system prompt contains this explicit rule:
> "False positives (flagging a legitimate message as fraud) are worse than missing a fraud. When in doubt, verdict LEGITIMATE."

This directly encodes our primary eval metric (false positive rate) into Claude's behaviour. A fraud detector that flags too many legitimate messages loses user trust and gets ignored. Better to catch 8 out of 10 frauds reliably than to flag everything aggressively.

---

## How to run

```bash
cd backend
python3 rag_pipeline.py
```

Requires `ANTHROPIC_API_KEY` set in `backend/.env`. Patterns must already be ingested (Step 1). If ChromaDB is empty, call `ingest_patterns()` first.
