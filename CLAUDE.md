# WhatsApp Fraud Detector — Claude Code Instructions

## What this project is

A portfolio prototype demonstrating AI-powered fraud detection for WhatsApp messages.
Built by Nibhrit Mohanty (MBA, IIM Mumbai / former PayPal SDE) as a PM interview portfolio piece.

**What it is NOT:** A live WhatsApp integration. This demonstrates the detection logic that WhatsApp would need to build natively.

---

## Stack — do not suggest alternatives

| Layer | Choice | Reason |
|-------|--------|--------|
| LLM | Claude API (Haiku model) | Cost-efficient, handles Hinglish natively |
| Backend | FastAPI (Python) | Lightweight, easy to deploy |
| Vector DB | ChromaDB | Local, no account needed |
| Embeddings | OpenAI text-embedding-ada-002 OR Claude embeddings | For RAG pipeline |
| Frontend | Single HTML file | Portfolio-shareable, no framework needed |
| Deployment | Render (backend) + GitHub Pages (frontend) | Free tier, live URL for portfolio |

Never suggest Streamlit, OpenAI GPT models, LangChain, or Flask as alternatives unless explicitly asked.

---

## Folder structure

```
whatsapp-fraud-detector/
├── CLAUDE.md
├── backend/
│   ├── main.py              # FastAPI app — single /analyse endpoint
│   ├── rag_pipeline.py      # ChromaDB retrieval + Claude LLM call
│   ├── fraud_patterns.py    # Pattern ingestion into ChromaDB
│   └── requirements.txt
├── frontend/
│   └── index.html           # Landing page + embedded WhatsApp demo UI
├── data/
│   └── fraud_patterns.txt   # Raw fraud pattern library
├── evals/
│   ├── evals.py             # Evaluation script
│   └── test_messages.json   # 30 test messages (15 fraud, 15 legit)
├── learnings/
│   └── stepN_short_name.md  # One doc per build step — concepts, decisions, how-to-run
└── README.md
```

---

## API contract — do not change without flagging

`POST /analyse`

Input:
```json
{ "message": "..." }
```

Output:
```json
{
  "verdict": "FRAUD",
  "confidence": 91,
  "pattern": "UPI KYC Expiry Scam",
  "explanation": "...",
  "recommendation": "...",
  "language": "hinglish"
}
```

The `language` field must always be returned. Explanation and recommendation must be written in the detected language of the input message (English / Hindi / Hinglish).

---

## Fraud pattern library — v1 scope

5 categories, ~4-5 sub-patterns each (~22 total). Do not add categories beyond these 5 for v1:

1. UPI / KYC Fraud
2. Fake Job Offers
3. Lottery / Prize Scams
4. Bank Impersonation
5. Investment Fraud

---

## Eval standard

- 30 test messages: 15 fraud, 15 legit
- Mix of English, Hindi, Hinglish across the set
- **Primary metric: False positive rate** (flagging legit messages as fraud)
- Secondary: precision, recall, explanation quality (manual 1–5 score)

---

## Explicitly out of scope for v1

- Real WhatsApp integration or message interception
- User accounts, login, or message history
- Mobile responsive design
- More than 5 fraud categories
- Any LangChain dependency

---

## Working style — follow in every session

1. **One layer at a time.** Build and verify each component before moving to the next. Order: pattern library → RAG pipeline → Claude integration → FastAPI endpoint → evals → HTML frontend → deployment.
2. **Explain after every component.** After writing any non-trivial code, explain what it does and why that design choice was made. The user needs to own every layer for interviews.
3. **Flag product decisions explicitly.** When making a choice about what to include, cut, or prioritise — name it as a product decision and give the reasoning.
4. **Features discussion before code.** If a new feature comes up mid-build, discuss and confirm before implementing.
5. **Write a learnings doc after every step.** When a build step is complete and verified, create a markdown file in the `learnings/` folder documenting: what was built, what each file does, key concepts introduced (explained plainly), and any product decisions made. File naming convention: `stepN_short_name.md` (e.g. `step2_rag_pipeline.md`). This is a permanent requirement — do not skip it.

---

## Deployment notes

- API key stored as environment variable on Render — never hardcoded
- Frontend calls backend via the Render URL (set as a JS constant at top of index.html)
- Disclaimer strip must be present on all versions of the frontend: "Work sample built by Nibhrit Mohanty — Not official WhatsApp content"
