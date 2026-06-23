import os
import json
import anthropic
from dotenv import load_dotenv
from fraud_patterns import ingest_patterns, retrieve_patterns

load_dotenv()

_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a fraud detection expert specialising in WhatsApp scams targeting Indian users.

Your job is to analyse a WhatsApp message and determine whether it is a scam.

You will be given:
1. The message to analyse
2. The 3 most semantically similar fraud patterns from a knowledge base — use these as reference, but similarity alone is not proof of fraud

STEP 1 — Detect language from the input message script:
- Any Devanagari characters present (क ख ग…) → language = "hindi"
- No Devanagari, but Hindi words in Roman script (bhai, aapka, hai, karein, abhi, nahi, etc.) → language = "hinglish"
- Fully English → language = "english"

STEP 2 — Write explanation and recommendation in that language:
- hindi → Devanagari script. Example: "यह एक KYC घोटाला है।"
- hinglish → Roman letters but Hindi words, like you are typing on WhatsApp. Example explanation: "Yeh ek fraud hai, aapko dara ke paise maange ja rahe hain." Example recommendation: "Koi bhi link pe click mat karein."
- english → Plain English.

STEP 3 — Respond ONLY with a valid JSON object, no markdown, no text outside the JSON:
{
  "verdict": "FRAUD" or "SUSPICIOUS" or "LEGITIMATE",
  "confidence": <integer 0-100>,
  "pattern": "<matched fraud pattern name, or 'None' if not fraud>",
  "explanation": "<max 12 words, in the language from STEP 1>",
  "recommendation": "<max 12 words, in the language from STEP 1>",
  "language": "<from STEP 1>"
}

Verdict rules:
- FRAUD: confidence ≥ 75, clear match to a known scam pattern.
- SUSPICIOUS: confidence 40–74, red flags present but not certain.
- LEGITIMATE: no strong fraud signals. When in doubt, verdict LEGITIMATE.
- False positives are worse than missed fraud.
- Confidence should reflect real certainty — do not inflate it."""


def _build_user_message(message: str, retrieved: list[dict]) -> str:
    pattern_block = "\n\n".join(
        f"Pattern {i + 1}: [{r['pattern']}] — {r['category']}\n{r['text']}"
        for i, r in enumerate(retrieved)
    )
    return (
        f"RETRIEVED FRAUD PATTERNS (most semantically similar to the input message):\n\n"
        f"{pattern_block}\n\n"
        f"---\n\n"
        f"MESSAGE TO ANALYSE:\n{message}"
    )


def _strip_fences(text: str) -> str:
    """Claude sometimes wraps JSON in markdown code fences despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def analyse(message: str) -> dict:
    retrieved = retrieve_patterns(message, n_results=3)
    user_message = _build_user_message(message, retrieved)

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = _strip_fences(response.content[0].text)
    result = json.loads(raw)
    return result


if __name__ == "__main__":
    ingest_patterns()

    test_cases = [
        # --- Fraud ---
        "Congratulations! Your UPI ID has been selected for a reward of Rs 50,000. Click here to claim: http://upi-reward.xyz",
        "Aapka bijli connection aaj raat kat jayega. Abhi is number pe call karein: 9876543210",
        "I am Sarah from Amazon HR. You have been selected for WFH role. Salary 45k/month. Pay Rs 500 registration fee to proceed.",
        "KBC lottery winner! Your number has won Rs 25 lakh. Pay Rs 2000 processing fee to claim. Contact: 8800XXXXXX",
        # --- Legitimate ---
        "Hey, are we still on for dinner at 8?",
        "Bhai kal cricket dekhne chalein? India vs Australia match hai",
        "Your OTP for Swiggy login is 847291. Valid for 10 minutes. Do not share with anyone.",
        "Mom, I'll be home by 7. Don't wait for me for dinner.",
    ]

    print("\n" + "=" * 65)
    for msg in test_cases:
        result = analyse(msg)
        label = "FRAUD" if result["verdict"] == "FRAUD" else "LEGIT"
        print(f"\n[{label}] {result['confidence']}% — {result['pattern']}")
        print(f"  Msg  : {msg[:70]}")
        print(f"  Lang : {result['language']}")
        print(f"  Why  : {result['explanation'][:90]}")
        print(f"  Do   : {result['recommendation'][:90]}")
    print("\n" + "=" * 65)
