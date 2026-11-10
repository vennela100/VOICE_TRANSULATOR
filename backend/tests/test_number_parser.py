from decimal import Decimal

import pytest

from app.meaning.number_parser import parse_number


@pytest.mark.parametrize(
    ("text", "expected", "currency"),
    [
        ("Rs 1,25,000", 125000, True),
        ("₹1,25,000", 125000, True),
        ("₹१,२५,०००", 125000, True),
        ("రూ. ౧,౨౫,౦౦౦", 125000, True),
        ("12345 rupees", 12345, True),
        ("1.25 lakh rupees", 125000, True),
        ("50 thousand", 50000, False),
        ("fifty thousand rupees", 50000, True),
        ("one lakh fifty thousand rupees", 150000, True),
        ("do lakh pachaas hazaar rupaye", 250000, True),
        ("paanch hazaar rupaye", 5000, True),
        ("पाँच हजार रुपये", 5000, True),
        ("दो लाख पचास हजार", 250000, False),
        ("सवा लाख", 125000, False),
        ("सवा लाख रुपये", 125000, True),
        ("sava lakh rupaye", 125000, True),
        ("dedh lakh", 150000, False),
        ("डेढ़ लाख रुपये", 150000, True),
        ("dedh hazaar", 1500, False),
        ("ढाई हजार रुपये", 2500, True),
        ("dhai hazaar", 2500, False),
        ("paune do lakh", 175000, False),
        ("पौने दो लाख रुपये", 175000, True),
        ("sadhe teen hazaar", 3500, False),
        ("साढ़े तीन हजार", 3500, False),
        ("तीन सौ", 300, False),
        ("pachaas hazaar", 50000, False),
        ("ninety nine rupees", 99, True),
        ("one crore", 10000000, False),
        ("do crore pachaas lakh", 25000000, False),
        # Telugu word forms below are intentionally unverified. The parser may
        # extract a candidate value, but must always request confirmation.
        ("rendu vela rupayalu", 2000, True),
        ("aidhu vandalu", 500, False),
        ("okati lakh", 100000, False),
        ("రెండు వేల రూపాయలు", 2000, True),
        ("ఐదు వందలు", 500, False),
        ("ఒక లక్ష", 100000, False),
        ("యాభై వేల రూపాయలు", 50000, True),
        ("లక్ష ఇరవై ఐదు వేలు", 125000, False),
        ("రూ ౫౦౦", 500, True),
        ("₹१२३", 123, True),
        ("twelve thousand five hundred", 12500, False),
        ("ek sau pachis", 125, False),
        ("nineteen hundred", 1900, False),
        ("तीन करोड़", 30000000, False),
        ("నాలుగు వేలు", 4000, False),
    ],
)
def test_number_parser_values_and_currency(text, expected, currency):
    parsed = parse_number(text)
    assert parsed is not None
    assert parsed.normalized_value == Decimal(expected)
    assert parsed.is_currency is currency
    assert parsed.source_span
    if text.startswith(("rendu", "aidhu", "okati", "రెండు", "ఐదు", "ఒక ", "యాభై", "లక్ష", "నాలుగు")):
        assert parsed.needs_confirmation


def test_sava_lakh_is_formatted_in_indian_grouping():
    parsed = parse_number("sava lakh rupaye")
    assert parsed.formatted == "Rs 1,25,000"
    assert parsed.source_span.lower() == "sava lakh rupaye"


def test_telugu_word_mapping_is_explicitly_unverified():
    parsed = parse_number("రెండు వేల రూపాయలు")
    assert parsed.needs_confirmation is True
    assert parsed.mapping_status == "provisional"


def test_hindi_word_mapping_is_not_mislabeled_as_verified():
    parsed = parse_number("पाँच हजार रुपये")
    assert parsed.mapping_status == "inferred"


def test_digit_with_word_scale_is_marked_as_inferred():
    parsed = parse_number("50 thousand")
    assert parsed.mapping_status == "inferred"


def test_digits_only_are_marked_as_literal():
    parsed = parse_number("₹50,000")
    assert parsed.mapping_status == "literal"


def test_unanchored_fraction_requires_confirmation():
    parsed = parse_number("sava")
    assert parsed is not None
    assert parsed.needs_confirmation is True


def test_conflicting_spoken_and_digit_amount_is_ambiguous():
    parsed = parse_number("pachaas hazaar, 60,000 rupees")
    assert parsed is not None
    assert parsed.needs_confirmation is True
    assert parsed.ambiguous is True


def test_unrecognized_text_has_no_number():
    assert parse_number("please call me tomorrow") is None
