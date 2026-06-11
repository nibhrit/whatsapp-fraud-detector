# Step 5: HTML Frontend

## What we built

`frontend/index.html` — a single self-contained HTML file that serves as both the portfolio landing page and the live demo environment.

---

## Page structure

| Section | Purpose |
|---------|---------|
| Disclaimer strip | Amber, sticky — "Work sample built by Nibhrit Mohanty — Not official WhatsApp content" |
| Nav | Logo + anchor links to sections |
| Hero | Problem statement, key stats, phone mockup preview |
| How it works | 3-step product explanation |
| Tech stack | 4 cards — Claude Haiku, ChromaDB, RAG Pipeline, FastAPI |
| Evals strip | Dark green band — 4 metrics from Step 4 |
| Live demo | WhatsApp mock UI with pre-loaded messages + user input |
| Footer | Name, GitHub link, disclaimer |

---

## The WhatsApp UI

The chat interface is built in pure HTML/CSS — no external libraries. Key design choices:

- **Colors match WhatsApp exactly:** `#075E54` (header), `#ECE5DD` (chat background), `#FFFFFF` (message bubbles)
- **Each incoming message has a 🛡 Analyse button** — the user activates analysis per message, not automatically
- **Result card slides in inline** below the analysed bubble — not in a panel or popup
- **Input bar at the bottom** — user can paste any message and add it to the chat as a new incoming bubble to test

### Pre-loaded messages (6)

| Message | Language | Type |
|---------|----------|------|
| UPI reward Rs 50,000 link | English | Fraud |
| KYC expiry warning | Hinglish | Fraud |
| Swiggy OTP | English | Legitimate |
| Amazon HR job with deposit | English | Fraud |
| Cricket ticket invite | Hinglish | Legitimate |
| RBI legal threat | Hindi | Fraud |

These were chosen to show a mix of fraud types, languages, and one tricky legitimate case (OTP) upfront.

---

## How the JS works

Three key functions:

**`init()`** — runs on page load. Renders all pre-loaded messages into the chat with their shield buttons.

**`addUserMessage()`** — reads the input field, creates a new incoming message bubble, and appends it to the chat. Triggered by Enter key or send button.

**`analyse(id, btn)`** — async function that:
1. Disables the shield button and shows a loading spinner
2. Calls `POST /analyse` on the backend with the message text
3. On success: renders the result card and hides the shield button
4. On error: shows a friendly error with instructions to start the backend

**`renderResult(id, data)`** — builds the AI Shield card HTML from the API response. Applies `.fraud` or `.legit` CSS class for colour coding. Smoothly scrolls the result into view.

---

## Key design decisions

### AI Shield is opt-in per message, not automatic

The user taps 🛡 on a specific message. This is a deliberate product decision:
- Automatic analysis of every message would feel surveillance-like
- User control is a core privacy principle
- Mirrors how WhatsApp actually surfaces optional features (long-press → action)

This maps directly to the interview framing: *"The AI only acts when asked. Privacy-first design."*

### Single HTML file

No build step, no npm, no framework. Anyone can open the file. This is the right choice for a portfolio project — portability over architecture.

### API_URL constant at the top of the script

```javascript
const API_URL = "http://localhost:8000"; // swap to Render URL after deployment
```

One line to change when deploying. The frontend doesn't care where the backend lives — it just needs this URL to be correct.

### Result language matches input automatically

The backend detects the language and Claude responds in it. The frontend just displays whatever text comes back — no language-specific logic needed on the frontend side.

---

## How to run locally

```bash
# Terminal 1 — backend
cd backend
python3 -m uvicorn main:app

# Terminal 2 — frontend (serves via HTTP, required for CORS to work)
cd frontend
python3 -m http.server 3000
# then open: http://localhost:3000
```

Note: opening `index.html` directly as a `file://` URL will cause CORS errors when the JS tries to call the API. Always serve it through a local HTTP server during development.

---

## What changes at deployment

1. Deploy backend to Render — get a URL like `https://your-app.onrender.com`
2. In `index.html`, change line: `const API_URL = "http://localhost:8000"` → `const API_URL = "https://your-app.onrender.com"`
3. Push `frontend/` to GitHub Pages
4. Done — anyone with the GitHub Pages URL can use the live demo
