# Step 6: Deployment

## What we built

Three config files that enable one-command deployment:

| File | Purpose |
|------|---------|
| `.gitignore` | Excludes `.env`, `chroma_db/`, `__pycache__` from git |
| `render.yaml` | Tells Render how to build and run the backend |
| `.github/workflows/deploy.yml` | GitHub Action that auto-deploys `frontend/` to GitHub Pages on every push to main |

---

## Architecture: two services, one live URL

```
User opens GitHub Pages URL
        ↓
frontend/index.html  (static, GitHub Pages — free)
        ↓  API call
backend/main.py      (FastAPI on Render — free tier)
        ↓
ChromaDB + Claude Haiku
```

The frontend and backend are deployed separately. They communicate over HTTP. The only connection point is `const API_URL` in `index.html`.

---

## Why two platforms instead of one?

- **GitHub Pages** only serves static files (HTML, CSS, JS). It cannot run Python.
- **Render** runs the Python backend. It can't cheaply serve a static site.
- Keeping them separate also means the frontend can be updated without touching the backend and vice versa.

---

## Key deployment decisions

### ChromaDB on Render free tier

Render's free tier has an **ephemeral filesystem** — data written to disk doesn't persist between restarts. This means the `chroma_db/` folder gets wiped each time the server cold-starts.

This is fine because:
- The fraud patterns are stored in `backend/fraud_patterns.py` (in code, committed to git)
- The `lifespan` function in `main.py` calls `ingest_patterns()` on every server start
- ChromaDB is rebuilt from scratch in ~2 seconds at startup

In production, you'd use a persistent volume or a managed vector DB. For this prototype, re-ingesting on startup is acceptable.

### The Render cold start problem

Render free tier sleeps after 15 minutes of inactivity. The first request after sleep takes ~30 seconds to wake up. 

**How to handle this in a demo:**
- Open the page yourself 30 seconds before showing it to someone
- Click any 🛡 Analyse button to wake the backend before your audience arrives
- After the first request, all subsequent ones respond in ~2-3 seconds

### Why `--host 0.0.0.0`

The start command is `uvicorn main:app --host 0.0.0.0 --port $PORT`. By default, uvicorn binds to `127.0.0.1` (localhost only). Render routes external traffic to the container, so the app must bind to `0.0.0.0` to accept that traffic. Without this, the service would start but all requests would fail.

### ANTHROPIC_API_KEY on Render

The API key is set as an environment variable in the Render dashboard — never in code, never in git. Render injects it into the container at runtime. The `load_dotenv()` call in `main.py` reads from `.env` locally; on Render, the OS environment variable takes precedence, so the `.env` file doesn't need to exist there.

---

## GitHub Actions workflow explained

```yaml
on:
  push:
    branches: [main]      # triggers on every push to main

permissions:
  pages: write            # allows writing to GitHub Pages
  id-token: write         # required for OIDC auth with Pages

jobs:
  deploy:
    steps:
      - checkout          # get the code
      - configure-pages   # set up Pages environment
      - upload-artifact   # bundle the frontend/ folder
        path: frontend    # THIS is what gets deployed
      - deploy-pages      # publish to your GitHub Pages URL
```

Every time you `git push`, this runs automatically. The frontend is live within ~60 seconds.

---

## Deployment steps (summary)

1. Create GitHub repo → push code
2. GitHub Settings → Pages → Source: GitHub Actions → first deploy runs automatically
3. Render → New Web Service → connect repo → set root dir, build/start commands, env var → deploy
4. Update `const API_URL` in `frontend/index.html` to Render URL → push → done

---

## Final URLs

- **Frontend:** `https://YOUR_USERNAME.github.io/whatsapp-fraud-detector/`
- **Backend:** `https://YOUR_APP.onrender.com`
- **API docs:** `https://YOUR_APP.onrender.com/docs` (FastAPI auto-generated)
