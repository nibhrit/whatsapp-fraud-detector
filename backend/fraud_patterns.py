import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

PATTERNS = [
    # ── UPI / KYC Fraud ──────────────────────────────────────────────────
    {
        "id": "upi_001",
        "category": "UPI / KYC Fraud",
        "pattern": "KYC Expiry Threat",
        "text": (
            "Fraudster claims the user's KYC is expiring and their UPI or bank account will be "
            "blocked unless they update immediately. Creates urgency with a short deadline. Shares "
            "a phishing link or asks for Aadhaar or PAN numbers directly. "
            "Key signals: KYC expiring, account will be blocked, update within 24 hours, click to complete KYC."
        ),
    },
    {
        "id": "upi_002",
        "category": "UPI / KYC Fraud",
        "pattern": "Electricity Bill Cutoff Threat",
        "text": (
            "Fraudster poses as an electricity board such as BESCOM or MSEB, claiming the user's "
            "power will be disconnected due to a pending bill or KYC issue. Sends a phone number "
            "to call or a UPI link to pay immediately. "
            "Key signals: bijli connection katega, electricity disconnected tonight, pay immediately, update meter KYC."
        ),
    },
    {
        "id": "upi_003",
        "category": "UPI / KYC Fraud",
        "pattern": "Bank Account Blocked",
        "text": (
            "Fraudster impersonates a bank, claiming the account has been temporarily blocked due "
            "to suspicious activity or failed KYC. Asks user to click a link or call a number to unblock. "
            "Key signals: account has been blocked, suspicious transaction detected, verify identity, account will be permanently closed."
        ),
    },
    {
        "id": "upi_004",
        "category": "UPI / KYC Fraud",
        "pattern": "Refund Pending Scam",
        "text": (
            "Fraudster tells the user a refund is pending and they need to enter their UPI PIN to "
            "receive it. This is reverse psychology — instead of sending money, the fraudster tricks "
            "the user into approving an outgoing payment request. "
            "Key signals: refund of Rs X is pending, enter UPI PIN to receive, click here to claim refund."
        ),
    },
    {
        "id": "upi_005",
        "category": "UPI / KYC Fraud",
        "pattern": "Payment Failed Recovery",
        "text": (
            "Fraudster claims a recent payment failed and offers a link to retry or claim cashback. "
            "The link leads to a fake payment page designed to capture UPI credentials. "
            "Key signals: your recent payment failed, click to retry, cashback pending, transaction incomplete."
        ),
    },

    # ── Fake Job Offers ───────────────────────────────────────────────────
    {
        "id": "job_001",
        "category": "Fake Job Offers",
        "pattern": "Work From Home High Pay",
        "text": (
            "Fraudster offers an unrealistically high-paying work-from-home job requiring no experience "
            "or qualifications. May ask for a registration fee or security deposit upfront. "
            "Key signals: earn 50000 per month from home, no experience needed, work 2 hours a day, registration fee refundable."
        ),
    },
    {
        "id": "job_002",
        "category": "Fake Job Offers",
        "pattern": "Government Job Guarantee",
        "text": (
            "Fraudster claims to offer a guaranteed government job such as UPSC, SSC, railway, or "
            "police in exchange for a processing or registration fee. Impersonates official government agencies. "
            "Key signals: government job guarantee, UPSC vacancy, railway recruitment, guaranteed selection, pay processing fee."
        ),
    },
    {
        "id": "job_003",
        "category": "Fake Job Offers",
        "pattern": "Data Entry / Mobile Task Job",
        "text": (
            "Fraudster offers simple typing, data entry, or like and subscribe tasks doable on mobile. "
            "Pays small amounts initially to build trust, then asks for an investment to unlock "
            "higher-paying tasks. "
            "Key signals: simple typing job, like and earn money, Rs 500 per hour, easy task, subscribe and get paid."
        ),
    },
    {
        "id": "job_004",
        "category": "Fake Job Offers",
        "pattern": "HR Impersonation",
        "text": (
            "Fraudster poses as HR from a reputable company such as Infosys, TCS, or Amazon, claims "
            "the user has been selected for a job, and asks for a security deposit or training fee. "
            "Key signals: selected for the post, send joining fee, training charges, security deposit refundable, offer letter attached."
        ),
    },

    # ── Lottery / Prize Scams ─────────────────────────────────────────────
    {
        "id": "lottery_001",
        "category": "Lottery / Prize Scams",
        "pattern": "Lucky Draw Winner",
        "text": (
            "Fraudster claims the user has won a prize such as an iPhone, car, or cash in a lucky "
            "draw they never entered. Asks for a processing fee or personal details to release the prize. "
            "Key signals: congratulations you have won, lucky draw winner, claim your iPhone, processing fee to release prize."
        ),
    },
    {
        "id": "lottery_002",
        "category": "Lottery / Prize Scams",
        "pattern": "KBC / TV Show Winner",
        "text": (
            "Fraudster impersonates KBC (Kaun Banega Crorepati) or another popular TV show, claiming "
            "the user's phone number was randomly selected as a winner. Asks for tax or processing "
            "fee before releasing prize money. "
            "Key signals: KBC lottery winner, Amitabh Bachchan, winning amount, pay tax to claim, your number selected."
        ),
    },
    {
        "id": "lottery_003",
        "category": "Lottery / Prize Scams",
        "pattern": "Survey Reward Scam",
        "text": (
            "Fraudster asks the user to complete a short survey and promises a cash reward. Collects "
            "personal data and then asks for bank details to transfer the reward. "
            "Key signals: complete survey and earn, Rs 5000 reward, 2-minute survey, fill form and get paid."
        ),
    },
    {
        "id": "lottery_004",
        "category": "Lottery / Prize Scams",
        "pattern": "Gift Card / Voucher Winner",
        "text": (
            "Fraudster claims the user has won a gift card or voucher from Amazon or Flipkart. "
            "Collects details and asks for a small fee or OTP to activate the voucher. "
            "Key signals: Amazon gift card winner, Flipkart voucher, Rs 10000 coupon, activate your reward."
        ),
    },

    # ── Bank Impersonation ────────────────────────────────────────────────
    {
        "id": "bank_001",
        "category": "Bank Impersonation",
        "pattern": "OTP Request",
        "text": (
            "Fraudster poses as a bank employee or customer support agent, claims there is a security "
            "issue with the account, and asks the user to share the OTP received on their phone. "
            "Key signals: share the OTP, verify your account, bank customer care calling, OTP for security check."
        ),
    },
    {
        "id": "bank_002",
        "category": "Bank Impersonation",
        "pattern": "Card Blocked Alert",
        "text": (
            "Fraudster sends an urgent message claiming the user's debit or credit card has been "
            "blocked due to suspicious activity. Asks user to call a number or click a link to unblock. "
            "Key signals: your card has been blocked, call immediately, card expired, reactivate your card."
        ),
    },
    {
        "id": "bank_003",
        "category": "Bank Impersonation",
        "pattern": "Account Suspended Notice",
        "text": (
            "Fraudster impersonates a bank claiming the user's account has been suspended due to KYC "
            "mismatch, suspicious activity, or a regulatory requirement. Creates panic to trigger "
            "impulsive action without thinking. "
            "Key signals: account suspended, KYC mismatch, regulatory requirement, account will be closed, verify within 24 hours."
        ),
    },
    {
        "id": "bank_004",
        "category": "Bank Impersonation",
        "pattern": "RBI / Legal Threat",
        "text": (
            "Fraudster poses as an RBI official or legal authority, claiming the user's account has "
            "been flagged for illegal activity and they must pay a fine or face arrest. Uses fear "
            "and authority to coerce payment. "
            "Key signals: RBI notice, legal action, account under investigation, pay penalty, CBI arrest warrant."
        ),
    },

    # ── Investment Fraud ──────────────────────────────────────────────────
    {
        "id": "invest_001",
        "category": "Investment Fraud",
        "pattern": "Guaranteed High Returns",
        "text": (
            "Fraudster promises guaranteed high returns on investment in a very short time. No "
            "legitimate investment can guarantee returns. Common in pyramid schemes and fake trading platforms. "
            "Key signals: double your money, 500% returns guaranteed, guaranteed profit, invest 1000 get 2000, risk-free investment."
        ),
    },
    {
        "id": "invest_002",
        "category": "Investment Fraud",
        "pattern": "Crypto Trading Group",
        "text": (
            "Fraudster invites the user to a WhatsApp or Telegram group where a trading expert gives "
            "tips. Initially shows fake profits to build trust, then asks for an investment which is stolen. "
            "Key signals: join crypto group, trading signals, expert trader, invest in Bitcoin, guaranteed crypto returns."
        ),
    },
    {
        "id": "invest_003",
        "category": "Investment Fraud",
        "pattern": "Stock Market Insider Tip",
        "text": (
            "Fraudster claims to have insider information on stocks that will give guaranteed returns. "
            "Asks user to invest through their platform or a shared link. "
            "Key signals: insider tip, stock will 10x, buy this share now, secret stock tip, made 10 lakh last month."
        ),
    },
    {
        "id": "invest_004",
        "category": "Investment Fraud",
        "pattern": "MLM / Pyramid Scheme",
        "text": (
            "Fraudster promotes a multi-level marketing or pyramid scheme promising passive income "
            "through referrals. User earns by recruiting others, not from any real product or service. "
            "Key signals: passive income, earn by referring, network marketing, join team and earn daily, downline earnings."
        ),
    },
]


def _get_collection():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name="fraud_patterns",
        embedding_function=DefaultEmbeddingFunction(),
    )
    return client, collection


def ingest_patterns():
    client, collection = _get_collection()

    if collection.count() == len(PATTERNS):
        print(f"Already ingested {len(PATTERNS)} patterns. Skipping.")
        return

    # Fresh ingest: delete collection and recreate to avoid duplicates
    client.delete_collection("fraud_patterns")
    _, collection = _get_collection()

    collection.add(
        ids=[p["id"] for p in PATTERNS],
        documents=[p["text"] for p in PATTERNS],
        metadatas=[{"category": p["category"], "pattern": p["pattern"]} for p in PATTERNS],
    )
    print(f"Ingested {len(PATTERNS)} patterns into ChromaDB.")


def retrieve_patterns(query: str, n_results: int = 3) -> list[dict]:
    _, collection = _get_collection()
    results = collection.query(query_texts=[query], n_results=n_results)
    return [
        {
            "pattern": results["metadatas"][0][i]["pattern"],
            "category": results["metadatas"][0][i]["category"],
            "text": results["documents"][0][i],
            "distance": results["distances"][0][i],
        }
        for i in range(len(results["ids"][0]))
    ]


if __name__ == "__main__":
    ingest_patterns()

    test_queries = [
        "aapka KYC expire ho raha hai account band ho jayega",
        "Congratulations! You have won an iPhone 15 in our lucky draw",
        "I am HR from TCS, you have been selected, send security deposit",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        matches = retrieve_patterns(query)
        for m in matches:
            print(f"  → [{m['category']}] {m['pattern']}  (distance: {m['distance']:.3f})")
