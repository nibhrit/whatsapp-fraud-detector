import json
import sys
import time
import requests

API_URL = "http://localhost:8000/analyse"


def run_evals(test_file: str = "evals/test_messages.json") -> None:
    try:
        requests.get("http://localhost:8000/health", timeout=3)
    except requests.exceptions.ConnectionError:
        print("ERROR: Backend is not running. Start it first:")
        print("  cd backend && python3 -m uvicorn main:app")
        sys.exit(1)

    with open(test_file) as f:
        cases = json.load(f)

    results = []
    print(f"Running {len(cases)} eval cases...\n")

    for case in cases:
        resp = requests.post(API_URL, json={"message": case["message"]}, timeout=30)
        r = resp.json()

        expected = case["expected"]
        got = r["verdict"]
        correct = expected == got

        results.append({
            "id": case["id"],
            "expected": expected,
            "got": got,
            "correct": correct,
            "confidence": r["confidence"],
            "pattern": r.get("pattern", ""),
            "language": r.get("language", ""),
            "category": case.get("category", ""),
            "message": case["message"],
        })

        status = "✓" if correct else "✗"
        label = f"{got} ({r['confidence']}%)"
        print(f"  {status} [{case['id']}] {label:<25} {case['message'][:55]}")
        time.sleep(0.5)

    _print_summary(results)
    _print_failures(results)


def _print_summary(results: list) -> None:
    fraud = [r for r in results if r["expected"] == "FRAUD"]
    legit = [r for r in results if r["expected"] == "LEGITIMATE"]

    tp = sum(1 for r in fraud if r["got"] == "FRAUD")
    fn = sum(1 for r in fraud if r["got"] == "LEGITIMATE")
    tn = sum(1 for r in legit if r["got"] == "LEGITIMATE")
    fp = sum(1 for r in legit if r["got"] == "FRAUD")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr       = fp / len(legit) if legit else 0
    accuracy  = (tp + tn) / len(results)

    print("\n" + "=" * 55)
    print("EVAL RESULTS")
    print("=" * 55)
    print(f"  Total messages : {len(results)} ({len(fraud)} fraud, {len(legit)} legit)")
    print(f"  Correct        : {tp + tn} / {len(results)}")
    print()
    print(f"  Accuracy       : {accuracy:.0%}")
    print(f"  Precision      : {precision:.0%}   (of flagged, how many were real fraud)")
    print(f"  Recall         : {recall:.0%}   (of real fraud, how many did we catch)")
    print()
    print(f"  ★ False Positive Rate : {fpr:.0%}   (legit messages wrongly flagged)")
    print()
    print(f"  True  Positives : {tp}   (fraud caught)")
    print(f"  False Negatives : {fn}   (fraud missed)")
    print(f"  True  Negatives : {tn}   (legit passed)")
    print(f"  False Positives : {fp}   (legit wrongly flagged)")
    print("=" * 55)


def _print_failures(results: list) -> None:
    failures = [r for r in results if not r["correct"]]
    if not failures:
        print("\nNo failures. All cases correct.")
        return

    print(f"\nFAILURES ({len(failures)}):")
    for r in failures:
        print(f"\n  [{r['id']}] expected={r['expected']} got={r['got']} ({r['confidence']}%)")
        print(f"  Category : {r['category']}")
        print(f"  Message  : {r['message'][:80]}")


if __name__ == "__main__":
    run_evals()
