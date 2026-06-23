import os
import re
import json
import anthropic
from dotenv import load_dotenv
from fraud_patterns import ingest_patterns, retrieve_patterns

load_dotenv()

_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Deterministic language detection ─────────────────────────────────────────
# Language detection is done in code, NOT by the LLM. Two reasons:
#   1. It must be reliable and testable — the LLM drifted (English messages
#      classified as Hinglish, Devanagari classified as Hinglish).
#   2. It frees the few-shot examples to anchor output STYLE only, without their
#      language mix biasing detection.
# The LLM is then TOLD the language and only has to write in it.

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")

# Romanised Hindi tokens that are distinctly Hindi (avoid words that collide with
# English like "is", "are", "main", "to"). One hit is enough to mark a Latin-script
# message as Hinglish.
_HINGLISH_TOKENS = {
    "aap", "aapka", "aapke", "aapki", "aapko", "hai", "hain", "nahi", "nahin",
    "kar", "karo", "karein", "karke", "karna", "kiya", "hota", "gaya", "gayi",
    "gaye", "raha", "rahi", "rahe", "mat", "bhai", "behen", "paisa", "paise",
    "paison", "abhi", "kya", "kyun", "mera", "meri", "mere", "tera", "teri",
    "tumhara", "yeh", "woh", "voh", "hum", "tum", "mein", "toh", "warna",
    "bhej", "bhejo", "bhejein", "chahiye", "rupaye", "rupay", "rupaiya",
    "zarurat", "zaroorat", "dunga", "denge", "wala", "wale", "wali", "kal",
    "aaj", "chalein", "chalo", "dekhne", "dekho", "jaldi", "turant", "jhooth",
    "dhokha", "theek", "accha", "achha", "matlab", "lekin", "agar", "magar",
    "phir", "sirf", "bahut", "thoda", "zyada", "ghante", "din", "raat",
}


def detect_language(message: str) -> str:
    """english | hindi | hinglish — deterministic, no LLM."""
    if _DEVANAGARI.search(message):
        return "hindi"
    words = set(re.findall(r"[a-z]+", message.lower()))
    if words & _HINGLISH_TOKENS:
        return "hinglish"
    return "english"


_STYLE_HINT = {
    "english": "Write explanation and recommendation in plain English.",
    "hindi": "Write explanation and recommendation in Hindi using Devanagari script (e.g. यह एक घोटाला है।).",
    "hinglish": (
        "Write explanation and recommendation in Hinglish — Hindi words spelled in "
        "Roman letters, exactly as people type on WhatsApp (e.g. \"Yeh ek fraud hai, "
        "link pe click mat karein.\"). Do NOT write them in plain English."
    ),
}

SYSTEM_PROMPT = """You are a fraud detection expert specialising in WhatsApp scams targeting Indian users.

Your job is to analyse a WhatsApp message and determine whether it is a scam.

You will be given:
1. The message to analyse
2. The language to respond in, plus a style instruction — follow it exactly
3. The 3 most semantically similar fraud patterns from a knowledge base — use these as reference, but similarity alone is not proof of fraud

Respond ONLY with a valid JSON object, no markdown, no text outside the JSON:
{
  "verdict": "FRAUD" or "SUSPICIOUS" or "LEGITIMATE",
  "confidence": <integer 0-100>,
  "pattern": "<matched fraud pattern name, or 'None' if not fraud>",
  "explanation": "<max 12 words, in the instructed language>",
  "recommendation": "<max 12 words, in the instructed language>",
  "language": "<the language you were told to use>"
}

Verdict rules:
- FRAUD: confidence ≥ 75, clear match to a known scam pattern.
- SUSPICIOUS: confidence 40–74, red flags present but not certain.
- LEGITIMATE: no strong fraud signals. When in doubt, verdict LEGITIMATE.
- False positives are worse than missed fraud.
- Confidence should reflect real certainty — do not inflate it."""


# The three examples below are deliberately ONE PER LANGUAGE (English, Hinglish, Hindi).
# This is the critical balance: they anchor the output STYLE for each language without
# biasing language DETECTION. Two examples of the same language pull detection toward it
# (e.g. two Hinglish examples made English/Hindi inputs wrongly classify as Hinglish).

# Example 1 — English fraud. Keeps English inputs in plain English.
_EXAMPLE_USER = (
    "RETRIEVED FRAUD PATTERNS (most semantically similar to the input message):\n\n"
    "Pattern 1: [Bank Account Block Threat] — Bank Impersonation\n"
    "Scammer claims the account will be blocked unless the user acts urgently.\n\n"
    "---\n\n"
    f"RESPOND IN: english\n{_STYLE_HINT['english']}\n\n"
    "---\n\n"
    "MESSAGE TO ANALYSE:\n"
    "Your SBI account has been blocked. Click this link now to update your KYC or you will lose access."
)
_EXAMPLE_ASSISTANT = json.dumps(
    {
        "verdict": "FRAUD",
        "confidence": 92,
        "pattern": "Bank Account Block Threat",
        "explanation": "Fake block threat pushing you to a phishing link.",
        "recommendation": "Do not click the link. Call your bank directly.",
        "language": "english",
    },
    ensure_ascii=False,
)

# Example 2 — Hinglish (non-fraud). Anchors Hinglish style AND shows that even
# neutral/suspicious analysis stays in Hinglish, not English.
_EXAMPLE_USER_2 = (
    "RETRIEVED FRAUD PATTERNS (most semantically similar to the input message):\n\n"
    "Pattern 1: [Loan Request] — Personal Request\n"
    "A contact asking the user to send money urgently.\n\n"
    "---\n\n"
    f"RESPOND IN: hinglish\n{_STYLE_HINT['hinglish']}\n\n"
    "---\n\n"
    "MESSAGE TO ANALYSE:\n"
    "Yaar mujhe abhi urgent 2000 rupaye chahiye, thodi der mein wapas kar dunga."
)
_EXAMPLE_ASSISTANT_2 = json.dumps(
    {
        "verdict": "SUSPICIOUS",
        "confidence": 55,
        "pattern": "None",
        "explanation": "Jaan-pehchaan wale ka paise maangna ho sakta hai, par account hack bhi ho sakta hai.",
        "recommendation": "Paise bhejne se pehle unhe call karke confirm karein.",
        "language": "hinglish",
    },
    ensure_ascii=False,
)

# Example 3 — Devanagari Hindi. Keeps Hindi inputs responding in Devanagari.
_EXAMPLE_USER_3 = (
    "RETRIEVED FRAUD PATTERNS (most semantically similar to the input message):\n\n"
    "Pattern 1: [KYC Expiry Scam] — UPI / KYC Fraud\n"
    "Scammer claims KYC is expiring to push the user into urgent action.\n\n"
    "---\n\n"
    f"RESPOND IN: hindi\n{_STYLE_HINT['hindi']}\n\n"
    "---\n\n"
    "MESSAGE TO ANALYSE:\n"
    "आपका KYC समाप्त हो रहा है। 24 घंटे में अपडेट करें वरना खाता बंद हो जाएगा।"
)
_EXAMPLE_ASSISTANT_3 = json.dumps(
    {
        "verdict": "FRAUD",
        "confidence": 90,
        "pattern": "KYC Expiry Scam",
        "explanation": "KYC बंद होने का डर दिखाकर जल्दबाज़ी में फँसाने की कोशिश है।",
        "recommendation": "किसी लिंक पर क्लिक न करें, अपने बैंक से सीधे संपर्क करें।",
        "language": "hindi",
    },
    ensure_ascii=False,
)


def _build_user_message(message: str, retrieved: list[dict], language: str) -> str:
    pattern_block = "\n\n".join(
        f"Pattern {i + 1}: [{r['pattern']}] — {r['category']}\n{r['text']}"
        for i, r in enumerate(retrieved)
    )
    return (
        f"RETRIEVED FRAUD PATTERNS (most semantically similar to the input message):\n\n"
        f"{pattern_block}\n\n"
        f"---\n\n"
        f"RESPOND IN: {language}\n{_STYLE_HINT[language]}\n\n"
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
    language = detect_language(message)
    retrieved = retrieve_patterns(message, n_results=3)
    user_message = _build_user_message(message, retrieved, language)

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _EXAMPLE_USER},
            {"role": "assistant", "content": _EXAMPLE_ASSISTANT},
            {"role": "user", "content": _EXAMPLE_USER_2},
            {"role": "assistant", "content": _EXAMPLE_ASSISTANT_2},
            {"role": "user", "content": _EXAMPLE_USER_3},
            {"role": "assistant", "content": _EXAMPLE_ASSISTANT_3},
            {"role": "user", "content": user_message},
        ],
    )

    raw = _strip_fences(response.content[0].text)
    result = json.loads(raw)
    # Language is decided in code, not by the LLM — it is authoritative.
    result["language"] = language
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
