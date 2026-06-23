# Step 7: Fixing Language Detection — Deterministic Code vs LLM Judgment

## The problem

Users reported that the detector kept responding in the wrong language:

1. First: English and Hinglish messages were getting **Hindi (Devanagari)** responses — bad for English speakers.
2. After a fix: Hinglish was detected correctly but the response came back in **pure English** — no Hindi words at all.
3. After another fix: the *explanation* field came in English while the *recommendation* came in Hinglish — inconsistent within the same card.
4. After yet another fix: detection itself broke — pure-English and Devanagari messages were wrongly classified as **Hinglish**.

It took several iterations to settle. The lesson in *why* is more valuable than the fix itself.

---

## Why it kept breaking — the root cause

We were asking the LLM to do **two conflicting jobs in a single call**:

- **Detect** the language of the message (english / hindi / hinglish)
- **Write** the explanation and recommendation in that language

To fix the *writing* style (Hinglish output kept reverting to English), the natural tool is a **few-shot example** — show the model a sample input and the ideal output. That works: examples steer output style far more reliably than instructions do.

But here's the trap: **few-shot examples also bias the detection.** When we added two Hinglish examples to fix the writing, the model started classifying *everything* — including clean English and Devanagari Hindi — as Hinglish, because the examples tilted its sense of "what these messages usually are."

Every fix to one job broke the other. This is the classic sign that **two responsibilities are tangled together and need to be separated.**

---

## The fix: move detection into deterministic code

Language detection does not actually need an LLM. It is a mechanical question about *which script and words* a message uses:

```python
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")   # Unicode block for Devanagari

_HINGLISH_TOKENS = {"aap", "hai", "nahi", "bhai", "paise", "karein", ...}

def detect_language(message: str) -> str:
    if _DEVANAGARI.search(message):
        return "hindi"                       # any Devanagari char → Hindi
    words = set(re.findall(r"[a-z]+", message.lower()))
    if words & _HINGLISH_TOKENS:
        return "hinglish"                    # romanised Hindi word present
    return "english"                         # otherwise plain English
```

- **Hindi** is trivial: if any character falls in the Devanagari Unicode block, it's Hindi. 100% reliable.
- **Hinglish vs English** is a word check: a curated set of distinctly-Hindi romanised tokens (`aap`, `hai`, `bhai`, `paise`…). We deliberately excluded words that collide with English (`is`, `are`, `main`, `to`) to avoid false positives.

This scored **10/10** on the test set, runs instantly, and is fully testable without any API call.

---

## How the LLM is used now

The model is no longer asked to detect anything. The pipeline:

1. `detect_language(message)` runs in code → gives the authoritative language.
2. That language + a style hint is **injected into the prompt**: *"RESPOND IN: hinglish — Hindi words in Roman letters, like WhatsApp typing."*
3. The model only has to **write** the verdict in the language it was told.
4. After parsing, we **overwrite** `result["language"]` with the code's answer, so the field can never drift:

```python
result["language"] = language  # code is authoritative, not the LLM
```

Now the few-shot examples (one English, one Hinglish, one Hindi) are free to anchor *only the writing style* — they can't corrupt detection anymore, because detection isn't the model's job.

---

## Key concepts introduced

### Separation of concerns
When one component has to satisfy two goals that pull against each other, splitting them is usually the real fix — not tuning the shared component harder. Here, detection (deterministic) and phrasing (generative) are genuinely different kinds of work and belong in different places.

### Use the LLM only for what needs an LLM
LLMs are for judgment and language generation. A script/word check is not judgment — it's a rule. Putting a rule into an LLM makes it *less* reliable, not more, and harder to test. Reserve the model for the fuzzy part (is this a scam? how do I phrase the warning?) and let code handle the crisp part.

### Few-shot examples steer everything, not just what you intend
An example doesn't only teach output format — it shifts the model's priors about the whole task, including classifications you weren't trying to change. Balance your examples, or remove the classification from the model entirely.

### Test before you ship
Most of the wasted iterations came from pushing prompt tweaks to the live server and asking the user to test. Running the pipeline locally and printing the actual output turned blind guessing into a measured fix in one pass.

---

## Product decisions made

- **Language detection is deterministic, not AI-driven.** Flagged as a product/engineering decision: it makes the `language` field testable, debuggable, and immune to model drift between runs. In an interview this is a clean story — "I used the LLM only where judgment was needed and kept mechanical logic in code."
- **Hinglish token list is curated to avoid English collisions.** Accepts a rare miss (a Hinglish message using only ambiguous words falls back to English) in exchange for never wrongly flagging a clean English message as Hinglish — consistent with the project's bias that a bad experience for English speakers is the thing to avoid.

---

## Files changed

| File | Change |
|------|--------|
| `backend/rag_pipeline.py` | Added `detect_language()` + `_STYLE_HINT`; rewrote system prompt to take language as an input; injected language into the user message; overwrite `result["language"]` with the code-detected value; balanced few-shot examples to one per language |
