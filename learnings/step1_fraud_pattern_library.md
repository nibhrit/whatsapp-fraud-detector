# Step 1: Fraud Pattern Library

## What we built

Two files:

| File | Purpose |
|------|---------|
| `data/fraud_patterns.txt` | Human-readable reference document — the pattern library as a product artefact |
| `backend/fraud_patterns.py` | The same patterns as structured Python data, plus functions to load them into ChromaDB and retrieve from it |

---

## The pattern library

21 patterns across 5 fraud categories:

| Category | Sub-patterns |
|----------|-------------|
| UPI / KYC Fraud | KYC Expiry Threat, Electricity Bill Cutoff, Bank Account Blocked, Refund Pending Scam, Payment Failed Recovery |
| Fake Job Offers | Work From Home High Pay, Government Job Guarantee, Data Entry / Mobile Task Job, HR Impersonation |
| Lottery / Prize Scams | Lucky Draw Winner, KBC / TV Show Winner, Survey Reward Scam, Gift Card / Voucher Winner |
| Bank Impersonation | OTP Request, Card Blocked Alert, Account Suspended Notice, RBI / Legal Threat |
| Investment Fraud | Guaranteed High Returns, Crypto Trading Group, Stock Market Insider Tip, MLM / Pyramid Scheme |

Each pattern is stored as a descriptive paragraph (not just a name) so the embedding model can capture its full semantic meaning.

---

## Key concepts

### Embeddings

An embedding is a way of converting text into a list of numbers (a vector) that captures its meaning. Words and sentences that are semantically similar end up close together in this numerical space — even if they share no words.

Example: "You've won a lottery" and "Claim your prize now" share no words, but their embeddings are close because they mean similar things. This is what allows the system to catch fraud messages even when the exact phrasing varies.

### ChromaDB

ChromaDB is a vector database — a database designed specifically to store embeddings and retrieve them by similarity. When a new message arrives:
1. It is converted to an embedding (a vector of numbers)
2. ChromaDB finds the stored patterns whose embeddings are closest to the message's embedding
3. Those patterns are returned as the most likely matches

### Distance

ChromaDB returns a **distance score** alongside each match. Lower distance = more similar.

From our test:
```
Query: aapka KYC expire ho raha hai account band ho jayega
  → KYC Expiry Threat       distance: 0.883   ← correct match, much closer
  → KBC / TV Show Winner    distance: 1.373   ← 56% further away
```

The large gap between the #1 and #2 result is what gives the retrieval confidence. When the gap is small, the system is less certain which pattern applies.

### Why 3 results (n_results=3)?

We retrieve the top 3 closest patterns, not just the top 1. All 3 are passed to the LLM in the next step. This gives the LLM context: "these are the fraud types this message most resembles — now reason against them and give a verdict." Retrieving only 1 would make the LLM's job harder; retrieving 10 would flood the prompt with noise.

---

## What the embedding model is

ChromaDB's default embedding function uses a model called **all-MiniLM-L6-v2** — a small, fast sentence embedding model that runs locally on your machine. It downloaded (~79 MB) on the first run and is now cached. Every subsequent run is instant.

This model understands semantic meaning across languages including Hinglish — demonstrated by our test:
```
Query (Hinglish): "aapka KYC expire ho raha hai account band ho jayega"
Matched (English pattern): "KYC Expiry Threat"
```
No translation step needed.

---

## Product decision: why not OpenAI embeddings?

We chose ChromaDB's built-in model over OpenAI's `text-embedding-ada-002`. The trade-offs:

| | ChromaDB default | OpenAI ada-002 |
|---|---|---|
| Cost | Free | ~$0.0001 per 1K tokens |
| API key needed | No | Yes (second key) |
| Works offline | Yes | No |
| English accuracy | Good | Better |
| Hinglish support | Good | Similar |

For a portfolio prototype with Indian language support, the built-in model is the right call. If this were a production system handling millions of messages, OpenAI or a fine-tuned multilingual model would be worth the cost.

---

## How to re-run

```bash
cd backend
python3 fraud_patterns.py
```

If patterns are already ingested, the script will skip ingestion and go straight to the retrieval test. To force a fresh ingest, delete the `backend/chroma_db/` folder and re-run.
