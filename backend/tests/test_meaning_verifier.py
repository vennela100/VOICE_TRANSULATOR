from app.meaning.entities import extract_critical_entities
from app.meaning.verifier import verify_translations


def test_amounts_extract_as_normalized_indian_values():
    result = extract_critical_entities("Please send Rs 1,25,000 tomorrow")
    assert result["amounts"][0]["normalized_value"] == "125000"
    assert result["amounts"][0]["formatted"] == "Rs 1,25,000"
    assert result["dates"][0]["normalized_value"] == "relative:tomorrow"


def test_supported_checks_never_claim_full_translation_is_verified():
    result = verify_translations("Send 500 rupees tomorrow", "500 rupees tomorrow")
    assert result["status"] == "ok"
    assert result["overall_meaning_verified"] is False
    assert "amounts_and_currency" in result["checks_scope"]


def test_mismatched_amount_blocks_delivery():
    result = verify_translations("Send Rs 50,000", "రూ. 60,000 పంపండి")
    assert result["status"] == "needs_confirmation"
    assert any(item["reason"] == "value_mismatch" for item in result["mismatches"])
    assert "confirm" in result["prompt_to_speaker"].lower()


def test_missing_amount_in_translation_blocks_delivery():
    result = verify_translations("भेजें पचास हजार रुपये", "దయచేసి పంపండి")
    assert result["status"] == "needs_confirmation"
    assert result["mismatches"][0]["reason"] == "missing_from_translation"


def test_extra_amount_in_translation_blocks_delivery():
    result = verify_translations("నమస్కారం", "రూ. 500 పంపండి")
    assert result["status"] == "needs_confirmation"
    assert result["mismatches"][0]["reason"] == "extra_in_translation"


def test_telugu_word_amount_always_requires_confirmation():
    result = verify_translations("రెండు వేల రూపాయలు", "రెండు వేల రూపాయలు")
    assert result["status"] == "needs_confirmation"
    assert result["entities_original"]["amounts"][0]["mapping_status"] == "provisional"


def test_same_absolute_date_and_time_match():
    result = verify_translations("Meet on 2026-06-15 at 2 PM", "2026-06-15 at 14:00")
    assert result["status"] == "ok"
    assert result["entities_original"]["dates"][0]["normalized_value"] == "2026-06-15"
    assert result["entities_original"]["times"][0]["normalized_value"] == "14:00"


def test_different_dates_and_times_block_delivery():
    result = verify_translations("Meet 15/06/2026 at 2 PM", "Meet 16/06/2026 at 3 PM")
    assert result["status"] == "needs_confirmation"
    assert any(item["kind"] == "date" for item in result["mismatches"])
    assert any(item["kind"] == "time" for item in result["mismatches"])


def test_ambiguous_day_month_date_requires_confirmation():
    result = extract_critical_entities("The appointment is 06/07/2026")
    assert result["dates"][0]["needs_confirmation"] is True


def test_relative_hindi_kal_is_flagged_as_ambiguous():
    result = extract_critical_entities("कल मिलते हैं")
    assert result["dates"][0]["needs_confirmation"] is True


def test_date_digits_are_not_reported_as_times_or_amounts():
    result = extract_critical_entities("Date 2026-06-15")
    assert result["amounts"] == []
    assert result["times"] == []


def test_mismatched_percentage_requires_confirmation_across_scripts():
    result = verify_translations(
        "The price rose by 5 percent",
        "\u0c35\u0c3f\u0c32\u0c41\u0c35 6 \u0c36\u0c3e\u0c24\u0c02",
    )
    assert result["status"] == "needs_confirmation"
    assert any(item["kind"] == "percentage" and item["reason"] == "value_mismatch"
               for item in result["mismatches"])


def test_measurements_normalize_common_unit_aliases():
    result = verify_translations("We need five kg", "We need 5 kilograms")
    assert result["status"] == "ok"
    assert result["entities_original"]["measurements"][0]["normalized_value"] == "5 mass:kg"


def test_quantity_mismatch_requires_confirmation():
    result = verify_translations("Bring 5 boxes", "Bring 10 boxes")
    assert result["status"] == "needs_confirmation"
    assert any(item["kind"] == "number" and item["reason"] == "value_mismatch"
               for item in result["mismatches"])


def test_phone_digits_normalize_across_indic_digit_scripts():
    telugu_digits = str.maketrans("0123456789", "\u0c66\u0c67\u0c68\u0c69\u0c6a\u0c6b\u0c6c\u0c6d\u0c6e\u0c6f")
    result = verify_translations("Call +91 98765 43210", "Call +91 98765 43210".translate(telugu_digits))
    assert result["status"] == "ok"
    assert result["entities_original"]["phone_numbers"][0]["normalized_value"] == "919876543210"


def test_negative_instruction_requires_speaker_confirmation():
    result = verify_translations(
        "Do not send the payment",
        "\u0c21\u0c2c\u0c4d\u0c2c\u0c41 \u0c2a\u0c02\u0c2a\u0c02\u0c21\u0c3f",
    )
    assert result["status"] == "needs_confirmation"
    assert any(item["kind"] == "negation" for item in result["mismatches"])


def test_detected_hindi_and_telugu_negation_markers_remain_unverified():
    result = verify_translations(
        "\u092a\u0948\u0938\u093e \u092e\u0924 \u092d\u0947\u091c\u094b",
        "\u0c21\u0c2c\u0c4d\u0c2c\u0c41 \u0c35\u0c26\u0c4d\u0c26\u0c41",
    )
    assert result["status"] == "needs_confirmation"
    assert result["entities_original"]["negations"][0]["mapping_status"] == "provisional"
    assert result["entities_translated"]["negations"][0]["mapping_status"] == "provisional"
