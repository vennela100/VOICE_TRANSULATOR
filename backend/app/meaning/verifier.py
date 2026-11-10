"""Deterministic comparison of critical entities before translated delivery."""

from __future__ import annotations

from decimal import Decimal

from app.meaning.entities import extract_critical_entities

SUPPORTED_CHECKS = [
    "amounts_and_currency",
    "dates_and_times",
    "percentages",
    "measurements_and_units",
    "phone_like_numbers",
    "other_parsed_numbers",
    "detected_negation_markers",
]


def verify_translations(original_text: str, translated_text: str) -> dict:
    original = extract_critical_entities(original_text)
    translated = extract_critical_entities(translated_text)
    mismatches: list[dict] = []
    needs_confirmation = False

    groups = (
        ("amounts", "amount"),
        ("dates", "date"),
        ("times", "time"),
        ("percentages", "percentage"),
        ("measurements", "measurement"),
        ("phone_numbers", "phone number"),
        ("numbers", "number"),
        ("negations", "negation"),
    )
    for group, kind in groups:
        source_entities = original[group]
        target_entities = translated[group]
        count = max(len(source_entities), len(target_entities))
        for index in range(count):
            source = source_entities[index] if index < len(source_entities) else None
            target = target_entities[index] if index < len(target_entities) else None
            if source is None:
                mismatches.append({"kind": kind, "reason": "extra_in_translation", "original": None, "translated": target})
                needs_confirmation = True
                continue
            if target is None:
                mismatches.append({"kind": kind, "reason": "missing_from_translation", "original": source, "translated": None})
                needs_confirmation = True
                continue
            if source["normalized_value"] != target["normalized_value"]:
                mismatches.append({"kind": kind, "reason": "value_mismatch", "original": source, "translated": target})
                needs_confirmation = True
            if source.get("needs_confirmation") or target.get("needs_confirmation"):
                needs_confirmation = True
                mismatches.append({"kind": kind, "reason": "ambiguous_or_unverified_mapping", "original": source, "translated": target})

    if needs_confirmation:
        prompt = _clarification_prompt(original, translated, mismatches)
        status = "needs_confirmation"
    else:
        prompt = None
        status = "ok"

    return {
        "status": status,
        # Passing this deterministic subset does not establish that the full
        # sentence or its unsupported entities were translated correctly.
        "overall_meaning_verified": False,
        "checks_scope": SUPPORTED_CHECKS,
        "entities_original": original,
        "entities_translated": translated,
        "mismatches": mismatches,
        "prompt_to_speaker": prompt,
    }


def _clarification_prompt(original: dict, translated: dict, mismatches: list[dict]) -> str:
    amount_mismatch = next((item for item in mismatches if item["kind"] == "amount"), None)
    if amount_mismatch:
        source = amount_mismatch.get("original")
        target = amount_mismatch.get("translated")
        if amount_mismatch["reason"] == "ambiguous_or_unverified_mapping" and source and source.get("source_span"):
            values = [source.get("formatted")]
            if source.get("normalized_value") != target.get("normalized_value") if target else False:
                values.append(target.get("formatted"))
            choices = " or ".join(value for value in values if value)
            return f"Please confirm the amount I heard: {choices}. You can confirm it or re-record."
        source_value = source.get("formatted") if source else "an amount"
        target_value = target.get("formatted") if target else "no amount"
        return f"I heard {source_value}, but the translation contains {target_value}. Please confirm the correct amount or re-record."

    if any(item["kind"] == "negation" for item in mismatches):
        return "I detected a possible negative or prohibiting statement. Please confirm its intended meaning before delivery."

    date_mismatch = next((item for item in mismatches if item["kind"] == "date"), None)
    if date_mismatch:
        source = date_mismatch.get("original")
        target = date_mismatch.get("translated")
        if date_mismatch["reason"] == "ambiguous_or_unverified_mapping":
            return f"Please confirm the date or time phrase: {source.get('source_span') if source else 'unclear date'}; then confirm or re-record."
        return f"The date differs between the transcript ({source.get('formatted') if source else 'missing'}) and translation ({target.get('formatted') if target else 'missing'}). Please confirm or re-record."

    time_mismatch = next((item for item in mismatches if item["kind"] == "time"), None)
    if time_mismatch:
        source = time_mismatch.get("original")
        target = time_mismatch.get("translated")
        return f"The time differs ({source.get('formatted') if source else 'missing'} vs {target.get('formatted') if target else 'missing'}). Please confirm or re-record."
    if mismatches:
        kind = mismatches[0]["kind"]
        return f"A critical {kind} may be missing, changed, or uncertain. Please confirm the detail or re-record."
    return "I could not safely verify a critical detail. Please confirm it or re-record."
