"""Deterministic number and currency parsing for Hindi, Telugu and English.

Word-based parses are labeled inferred; Telugu entries remain provisional.
Ambiguous parses and provisional Telugu results require speaker confirmation.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class NumberParseResult:
    normalized_value: Decimal
    formatted: str
    source_span: str
    is_currency: bool
    ambiguous: bool
    needs_confirmation: bool
    mapping_status: str
    alternatives: tuple[Decimal, ...] = ()


@dataclass(frozen=True)
class Token:
    text: str
    normalized: str
    start: int
    end: int
    is_digit: bool


_DIGIT_TRANSLATION = str.maketrans(
    "०१२३४५६७८९౦౧౨౩౪౫౬౭౮౯", "01234567890123456789"
)


def _fold(value: str) -> str:
    value = value.casefold().translate(_DIGIT_TRANSLATION)
    # Unicode normalization decomposes Indic vowel signs and nukta marks too.
    # Preserve those scripts byte-for-byte after case folding; normalize Latin
    # transliteration only.
    if any("DEVANAGARI" in unicodedata.name(ch, "") or "TELUGU" in unicodedata.name(ch, "") for ch in value):
        return value
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(ch)
    )


def _make_tokens(text: str) -> list[Token]:
    tokens = []
    index = 0
    while index < len(text):
        category = unicodedata.category(text[index])
        if text[index] == "₹":
            tokens.append(Token("₹", "₹", index, index + 1, False))
            index += 1
            continue
        if category.startswith("N"):
            start = index
            index += 1
            while index < len(text):
                next_category = unicodedata.category(text[index])
                if next_category.startswith("N"):
                    index += 1
                    continue
                if (
                    text[index] in ",.٫"
                    and index + 1 < len(text)
                    and unicodedata.category(text[index + 1]).startswith("N")
                ):
                    index += 1
                    continue
                break
            raw = text[start:index]
        elif category.startswith("L"):
            start = index
            index += 1
            while index < len(text) and unicodedata.category(text[index]).startswith(("L", "M")):
                index += 1
            raw = text[start:index]
        else:
            index += 1
            continue
        folded = _fold(raw)
        digit = all(
            character.isdigit() or character in ",.٫"
            for character in folded
        )
        normalized = folded.replace(",", "").replace("٫", ".") if digit else folded
        tokens.append(Token(raw, normalized, start, index, digit))
    return tokens


def _number_map(entries: dict[int, tuple[str, ...]]) -> dict[str, int]:
    return {word: value for value, words in entries.items() for word in words}


_NUMBERS = _number_map(
    {
        0: ("zero", "shunya", "शून्य", "शुन्य"),
        1: ("one", "a", "an", "ek", "eka", "एक", "१"),
        2: ("two", "do", "dho", "दो", "२"),
        3: ("three", "teen", "tin", "तीन", "३"),
        4: ("four", "char", "chaar", "चार", "४"),
        5: ("five", "paanch", "panch", "पांच", "पाँच", "५"),
        6: ("six", "chhe", "chhah", "छह", "६"),
        7: ("seven", "saat", "सात", "७"),
        8: ("eight", "aath", "आठ", "८"),
        9: ("nine", "nau", "नौ", "९"),
        10: ("ten", "das", "दस", "१०"),
        11: ("eleven", "gyarah", "ग्यारह"),
        12: ("twelve", "barah", "बारह"),
        13: ("thirteen", "terah", "तेरह"),
        14: ("fourteen", "chaudah", "चौदह"),
        15: ("fifteen", "pandrah", "पंद्रह", "पन्द्रह"),
        16: ("sixteen", "solah", "सोलह"),
        17: ("seventeen", "satrah", "सत्रह"),
        18: ("eighteen", "atharah", "अठारह"),
        19: ("nineteen", "unnees", "उन्नीस"),
        20: ("twenty", "bees", "बीस"),
        21: ("ikkees", "इक्कीस"),
        22: ("baees", "बाईस"),
        23: ("teis", "तेईस"),
        24: ("chaubees", "चौबीस"),
        25: ("twentyfive", "pachis", "pachis", "पच्चीस"),
        26: ("chhabis", "छब्बीस"),
        27: ("sattais", "सत्ताईस"),
        28: ("athais", "अट्ठाईस"),
        29: ("untees", "उनतीस"),
        30: ("thirty", "tees", "तीस"),
        31: ("ikattis", "इकतीस"),
        32: ("battis", "बत्तीस"),
        33: ("taintees", "तैंतीस"),
        34: ("chauntees", "चौंतीस"),
        35: ("paintis", "पैंतीस"),
        36: ("chhattis", "छत्तीस"),
        37: ("saintis", "सैंतीस"),
        38: ("adhtis", "अड़तीस"),
        39: ("untalis", "उनतालीस"),
        40: ("forty", "chalis", "चालीस"),
        41: ("iktalis", "इकतालीस"),
        42: ("bayalis", "बयालीस"),
        43: ("taitalis", "तैंतालीस"),
        44: ("chavalis", "चवालीस"),
        45: ("paitalis", "पैंतालीस"),
        46: ("chiyalis", "छियालीस"),
        47: ("saintalis", "सैंतालीस"),
        48: ("adhtalis", "अड़तालीस"),
        49: ("unchas", "उनचास"),
        50: ("fifty", "pachaas", "पचास"),
        60: ("sixty", "saath", "साठ"),
        70: ("seventy", "sattar", "सत्तर"),
        80: ("eighty", "assi", "अस्सी"),
        90: ("ninety", "nabbe", "नब्बे"),
    }
)

# Provisional spoken Telugu forms. Every parse using one of these is marked
# provisional and requires speaker confirmation until native review.
_TELUGU_NUMBERS = _number_map(
    {
        1: ("okati", "ఒకటి", "ఒక"),
        2: ("rendu", "రెండు"),
        3: ("moodu", "మూడు"),
        4: ("naalugu", "nalugu", "నాలుగు"),
        5: ("aidu", "aidhu", "ఐదు"),
        6: ("aaru", "ఆరు"),
        7: ("edu", "ఏడు"),
        8: ("enimidi", "ఎనిమిది"),
        9: ("tommidi", "తొమ్మిది"),
        10: ("padi", "పది"),
        20: ("iravai", "ఇరవై"),
        30: ("muppai", "ముప్పై"),
        40: ("nalabhai", "నలభై"),
        50: ("yaabhai", "యాభై"),
        60: ("aravai", "అరవై"),
        70: ("dabai", "డెబ్బై"),
        80: ("enabhai", "ఎనభై"),
        90: ("tombhai", "తొంభై"),
    }
)

_SCALES = {
    "hundred": 100,
    "hundreds": 100,
    "शत": 100,
    "sau": 100,
    "सौ": 100,
    "vanda": 100,
    "vandalu": 100,
    "వంద": 100,
    "వందలు": 100,
    "thousand": 1000,
    "thousands": 1000,
    "hazaar": 1000,
    "hazar": 1000,
    "हजार": 1000,
    "हज़ार": 1000,
    "veyyi": 1000,
    "vela": 1000,
    "veela": 1000,
    "velu": 1000,
    "వేలు": 1000,
    "వేల": 1000,
    "వెయ్యి": 1000,
    "lakh": 100000,
    "lakhs": 100000,
    "lac": 100000,
    "लाख": 100000,
    "लक्ष": 100000,
    "lakshalu": 100000,
    "లక్ష": 100000,
    "లక్షలు": 100000,
    "crore": 10000000,
    "crores": 10000000,
    "करोड़": 10000000,
    "करोड": 10000000,
    "koti": 10000000,
    "కోటి": 10000000,
    "కోట్లు": 10000000,
}

_CURRENCY = {
    "rs", "inr", "rupee", "rupees", "rupay", "rupaye", "rupaiya",
    "rupaya", "रुपये", "रुपया", "रुपए", "रूपये", "रूपया", "रु",
    "rupayalu", "ruupayalu", "రూపాయి", "రూపాయలు", "రూ", "₹",
}
_FRACTIONS = {
    "sava": (Decimal("0.25"), "add"),
    "sawa": (Decimal("0.25"), "add"),
    "सवा": (Decimal("0.25"), "add"),
    "sadhe": (Decimal("0.5"), "add"),
    "saadhe": (Decimal("0.5"), "add"),
    "साढ़े": (Decimal("0.5"), "add"),
    "साढे": (Decimal("0.5"), "add"),
    "paune": (Decimal("0.25"), "subtract"),
    "पौने": (Decimal("0.25"), "subtract"),
}
_SPECIAL_FRACTIONS = {
    "dedh": Decimal("1.5"),
    "डेढ़": Decimal("1.5"),
    "ढेढ़": Decimal("1.5"),
    "dhai": Decimal("2.5"),
    "ढाई": Decimal("2.5"),
}
_CONNECTORS = {"and", "aur", "और"}


def _token_value(token: Token) -> tuple[Decimal | None, bool, bool]:
    """Return value, is-number-word and is-unverified-Telugu."""
    if token.is_digit:
        try:
            return Decimal(token.normalized), False, False
        except Exception:
            return None, False, False
    if token.normalized in _NUMBERS:
        return Decimal(_NUMBERS[token.normalized]), True, False
    if token.normalized in _TELUGU_NUMBERS:
        return Decimal(_TELUGU_NUMBERS[token.normalized]), True, True
    return None, False, False


def _format_indian(value: Decimal, is_currency: bool) -> str:
    if value == value.to_integral_value():
        raw = str(abs(int(value)))
        if len(raw) > 3:
            tail, head = raw[-3:], raw[:-3]
            groups = []
            while len(head) > 2:
                groups.insert(0, head[-2:])
                head = head[:-2]
            raw = (head + ("," + ",".join(groups) if groups else "") + "," + tail)
        if value < 0:
            raw = "-" + raw
    else:
        raw = format(value.normalize(), "f")
    return f"Rs {raw}" if is_currency else raw


def _fraction_value(tokens: list[Token], index: int):
    token = tokens[index]
    word = token.normalized
    if word in _SPECIAL_FRACTIONS:
        value = _SPECIAL_FRACTIONS[word]
        end = index
        if index + 1 < len(tokens) and tokens[index + 1].normalized in _SCALES:
            end = index + 1
            value *= _SCALES[tokens[end].normalized]
        return value, end, False, False

    if word not in _FRACTIONS:
        return None
    fraction, operation = _FRACTIONS[word]
    next_index = index + 1
    if next_index >= len(tokens):
        return Decimal("1") + fraction, index, True, False

    next_token = tokens[next_index]
    if next_token.normalized in _SCALES:
        value = Decimal("1") + fraction
        return value * _SCALES[next_token.normalized], next_index, False, False

    next_value, _, unverified = _token_value(next_token)
    if next_value is None:
        return None
    end = next_index
    scale = None
    if next_index + 1 < len(tokens) and tokens[next_index + 1].normalized in _SCALES:
        scale = Decimal(_SCALES[tokens[next_index + 1].normalized])
        end = next_index + 1

    if operation == "subtract":
        value = next_value - fraction
    else:
        value = next_value + fraction
    if scale is not None:
        value *= scale
    return value, end, scale is None, unverified


def _parse_sequence(tokens: list[Token], start: int):
    fractional = _fraction_value(tokens, start)
    if fractional is not None:
        value, end, ambiguous, unverified = fractional
        return value, end, ambiguous, unverified, True, ()

    total = Decimal(0)
    current = Decimal(0)
    end = start - 1
    index = start
    saw_number = False
    saw_word_number = False
    word_mapping_used = False
    unverified = False
    has_explicit_digit = False
    conflict = False
    word_only_value = Decimal(0)
    word_current = Decimal(0)
    explicit_digits: list[Decimal] = []
    ambiguous = False

    while index < len(tokens):
        token = tokens[index]
        if token.normalized in _CONNECTORS and saw_number:
            end = index
            index += 1
            continue

        number, is_word, is_unverified = _token_value(token)
        if number is not None:
            # A digit after a complete word-number group is a second reading.
            # Compare it below instead of silently adding two contradictory forms.
            if token.is_digit:
                has_explicit_digit = True
                explicit_digits.append(number)
                if total > 0 and current == 0 and saw_word_number:
                    conflict = True
                    end = index
                    break
            else:
                saw_word_number = True
                word_mapping_used = True
                word_current += number
            saw_number = True
            current += number
            unverified = unverified or is_unverified
            end = index
            index += 1
            continue

        scale = _SCALES.get(token.normalized)
        if scale is not None:
            word_mapping_used = True
            if not saw_number:
                current = Decimal(1)
            if scale == 100:
                current *= scale
                if saw_word_number:
                    word_current *= scale
            else:
                total += current * scale
                current = Decimal(0)
                if saw_word_number:
                    word_only_value += word_current * scale
                    word_current = Decimal(0)
            saw_number = True
            end = index
            index += 1
            continue

        break

    if not saw_number:
        return None
    value = total + current
    word_only_value += word_current
    alternatives: tuple[Decimal, ...] = ()
    if conflict and explicit_digits:
        # Keep both readings for a clarification prompt. The spoken-word amount
        # is retained as the candidate but never delivered without confirmation.
        alternatives = tuple(dict.fromkeys([word_only_value, *explicit_digits]))
        ambiguous = True
    elif has_explicit_digit and saw_word_number and explicit_digits:
        if len(explicit_digits) == 1 and explicit_digits[0] != word_only_value:
            alternatives = (word_only_value, explicit_digits[0])
            value = word_only_value
            ambiguous = True
    return value, end, ambiguous, unverified, word_mapping_used, alternatives


def parse_number(text: str) -> NumberParseResult | None:
    """Parse the first Hindi, Telugu, English or digit-based number mention.

    Word mappings are never called verified: spoken forms are labeled inferred
    or provisional. Ambiguous readings and provisional Telugu parses require
    speaker confirmation. Currency text is included in the returned source span.
    """
    tokens = _make_tokens(text)
    for index, token in enumerate(tokens):
        if (
            token.normalized not in _CURRENCY
            and _token_value(token)[0] is None
            and token.normalized not in _SPECIAL_FRACTIONS
            and token.normalized not in _FRACTIONS
            and token.normalized not in _SCALES
        ):
            continue
        if token.normalized in _CURRENCY:
            continue

        parsed = _parse_sequence(tokens, index)
        if parsed is None:
            continue
        value, end_index, ambiguous, unverified, word_number, alternatives = parsed
        if value is None:
            continue

        start_index = index - 1 if index > 0 and tokens[index - 1].normalized in _CURRENCY else index
        currency_index = end_index + 1
        is_currency = any(
            tokens[item].normalized in _CURRENCY
            for item in range(start_index, min(len(tokens), end_index + 2))
        )
        if currency_index < len(tokens) and tokens[currency_index].normalized in _CURRENCY:
            end_index = currency_index
            is_currency = True

        span = text[tokens[start_index].start : tokens[end_index].end]
        return NumberParseResult(
            normalized_value=value,
            formatted=_format_indian(value, is_currency),
            source_span=span,
            is_currency=is_currency,
            ambiguous=ambiguous,
            # Hindi colloquial quarter/half forms need an explicit speaker
            # check even when the deterministic interpretation is parseable.
            needs_confirmation=ambiguous or unverified or token.normalized in _FRACTIONS or token.normalized in _SPECIAL_FRACTIONS,
            mapping_status=(
                "ambiguous" if ambiguous else
                "provisional" if unverified else
                "inferred" if word_number else
                "literal"
            ),
            alternatives=alternatives,
        )
    return None
