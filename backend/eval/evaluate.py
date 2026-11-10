"""Compute metrics only from supplied, measured CSV rows."""
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS = ROOT / "results.csv"


def wer(reference, hypothesis):
    ref, hyp = reference.split(), hypothesis.split()
    if not ref:
        return 0.0 if not hyp else 1.0
    prev = list(range(len(hyp) + 1))
    for i, token in enumerate(ref, 1):
        curr = [i]
        for j, predicted in enumerate(hyp, 1):
            curr.append(min(curr[-1] + 1, prev[j] + 1,
                            prev[j - 1] + (token.casefold() != predicted.casefold())))
        prev = curr
    return prev[-1] / len(ref)


def percentile(values, q):
    vals = sorted(values)
    if not vals: return None
    position = (len(vals) - 1) * q
    low = math.floor(position); high = math.ceil(position)
    return vals[low] if low == high else vals[low] * (high - position) + vals[high] * (position - low)


def main():
    if not RESULTS.exists():
        print(json.dumps({"sample_size": 0, "status": "No measured results.csv supplied.",
                          "instructions": "Record real utterances; fill the documented columns in results_template.csv."}, indent=2))
        return
    with RESULTS.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    valid_wer = [wer(r["reference_transcript"], r["stt_hypothesis"])
                 for r in rows if r.get("reference_transcript") and r.get("stt_hypothesis")]
    latencies = [float(r["latency_ms"]) for r in rows if r.get("latency_ms", "").strip()]
    rated = [float(r["human_translation_rating"]) for r in rows if r.get("human_translation_rating", "").strip()]
    completed = [r for r in rows if r.get("completed", "").strip()]
    preservation = [r for r in rows if r.get("critical_values_match", "").strip()]
    noise = defaultdict(list)
    for row in rows:
        if row.get("condition") and row.get("reference_transcript") and row.get("stt_hypothesis"):
            noise[row["condition"]].append(wer(row["reference_transcript"], row["stt_hypothesis"]))
    output = {
        "sample_size": len(rows),
        "stt_wer_sample_size": len(valid_wer),
        "stt_wer_mean": sum(valid_wer) / len(valid_wer) if valid_wer else None,
        "translation_rating_sample_size": len(rated),
        "translation_mean_rating_1_to_5": sum(rated) / len(rated) if rated else None,
        "critical_entity_sample_size": len(preservation),
        "critical_value_preservation_rate": sum(r["critical_values_match"].lower() in {"1", "true", "yes"} for r in preservation) / len(preservation) if preservation else None,
        "latency_sample_size": len(latencies), "latency_median_ms": percentile(latencies, .5),
        "latency_p95_ms": percentile(latencies, .95),
        "completion_sample_size": len(completed),
        "conversation_completion_rate": sum(r["completed"].lower() in {"1", "true", "yes", "delivered"} for r in completed) / len(completed) if completed else None,
        "wer_by_condition": {condition: sum(scores) / len(scores) for condition, scores in sorted(noise.items())},
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__": main()
