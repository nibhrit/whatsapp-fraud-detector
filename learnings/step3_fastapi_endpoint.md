# Step 3: FastAPI Endpoint

## What we built

`backend/main.py` — a lightweight HTTP server that exposes the RAG pipeline (Step 2) as an API any frontend can call over the internet.

---

## What each part does

### Pydantic models — request and response contracts

```python
class AnalyseRequest(BaseModel):
    message: str

class AnalyseResponse(BaseModel):
    verdict: str
    confidence: int
    ...
```

Pydantic models define the shape of what comes in and what goes out. FastAPI uses these to:
- Automatically validate incoming requests (if `message` is missing, it returns a 400 error)
- Automatically serialise the response to JSON
- Auto-generate API documentation at `/docs`

Think of them as the API contract enforced in code.

### Lifespan — startup logic

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    ingest_patterns()
    yield
```

This runs `ingest_patterns()` once when the server starts, ensuring ChromaDB is populated before any requests arrive. The `yield` separates startup (before) from shutdown (after). Without this, the first request could fail if ChromaDB hadn't been initialised yet.

### CORS middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

CORS (Cross-Origin Resource Sharing) is a browser security rule. By default, a browser blocks a web page from making API calls to a different domain. Our HTML frontend will be hosted on GitHub Pages (`nibhrit.github.io`) and our API will be on Render (`api.onrender.com`) — these are different origins, so the browser would block the request without CORS headers.

`allow_origins=["*"]` tells the browser: this API accepts requests from any origin. Fine for a portfolio project. In production, you'd restrict this to your frontend's exact domain.

### Health endpoint

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

Render (our deployment platform) periodically pings this endpoint to check the server is alive. If it returns anything other than 200, Render will restart the container. Standard practice for any deployed service.

### The main endpoint

```python
@app.post("/analyse", response_model=AnalyseResponse)
def analyse_message(request: AnalyseRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    result = analyse(request.message)
    return result
```

One endpoint, one job. Validates the input, calls `analyse()` from the RAG pipeline, returns the result. FastAPI handles JSON serialisation automatically via the `response_model`.

---

## Test results

```
GET  /health       → {"status": "ok"}

POST /analyse      (Hinglish KYC scam)
→ verdict: FRAUD, confidence: 85%, pattern: KYC Expiry Threat
→ explanation and recommendation returned in Hindi

POST /analyse      (casual lunch message)
→ verdict: LEGITIMATE, confidence: 99%, pattern: None
→ explanation in English
```

---

## How to run locally

```bash
cd backend
python3 -m uvicorn main:app --reload
```

`--reload` makes the server restart automatically when you edit a file. Useful during development, remove it in production.

The server runs at `http://localhost:8000`. You can also open `http://localhost:8000/docs` in a browser to see the auto-generated interactive API documentation — FastAPI generates this for free from the Pydantic models.

### Test with curl

```bash
curl -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"message": "Your KYC is expiring, click here to update"}'
```

---

## What the full stack looks like now

```
User message
     ↓
FastAPI /analyse endpoint  (main.py)
     ↓
retrieve_patterns()        (fraud_patterns.py → ChromaDB)
     ↓
analyse()                  (rag_pipeline.py → Claude Haiku)
     ↓
JSON response
```

All three layers are working end-to-end. The next step (evals) will stress-test this pipeline with 30 messages and give us real numbers to report.
