"""Deterministic extraction of critical amounts, dates and times."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal

from app.meaning.number_parser import parse_number


@dataclass(frozen=True)
class CriticalEntity:
    kind: str
    normalized_value: str
    source_span: str
    formatted: str
    needs_confirmation: bool = False
    mapping_status: str = "literal_or_deterministic_rule"

    def to_dict(self) -> dict:
        return asdict(self)


_DIGITS = str.maketrans("०१२३४५६७८९౦౧౨౩౪౫౬౭౮౯", "01234567890123456789")
_CURRENCY_HINTS = (
    "rs", "inr", "₹", "rupee", "rupay", "रुप", "रूप", "రూ", "రూపాయ",
)
_SCALE_HINTS = (
    "lakh", "lac", "लाख", "लक्ष", "లక్ష", "thousand", "hazaar", "हजार",
    "వేలు", "వెయ్యి", "crore", "करोड़", "koti", "కోటి",
)
_PERCENT_MARKERS = re.compile(
    r"(?iu)(%|percent(?:age)?|\u092a\u094d\u0930\u0924\u093f\u0936\u0924|\u0c36\u0c3e\u0c24\u0c02)"
)
_UNIT_ALIASES = {
    "kg": "mass:kg", "kilogram": "mass:kg", "kilograms": "mass:kg",
    "g": "mass:g", "gram": "mass:g", "grams": "mass:g",
    "mg": "mass:mg", "milligram": "mass:mg", "milligrams": "mass:mg",
    "km": "length:km", "kilometer": "length:km", "kilometers": "length:km",
    "kilometre": "length:km", "kilometres": "length:km",
    "cm": "length:cm", "centimeter": "length:cm", "centimeters": "length:cm",
    "centimetre": "length:cm", "centimetres": "length:cm",
    "mm": "length:mm", "millimeter": "length:mm", "millimeters": "length:mm",
    "millimetre": "length:mm", "millimetres": "length:mm",
    "ml": "volume:ml", "milliliter": "volume:ml", "milliliters": "volume:ml",
    "millilitre": "volume:ml", "millilitres": "volume:ml",
    "l": "volume:l", "liter": "volume:l", "liters": "volume:l",
    "litre": "volume:l", "litres": "volume:l",
    "°c": "temperature:c", "celsius": "temperature:c",
    "°f": "temperature:f", "fahrenheit": "temperature:f",
}
_UNIT_PATTERN = re.compile(
    r"(?iu)(?<!\w)(kg|kilograms?|g|grams?|mg|milligrams?|km|kilomet(?:er|re)s?|"
    r"cm|centimet(?:er|re)s?|mm|millimet(?:er|re)s?|ml|millilit(?:er|re)s?|"
    r"l|lit(?:er|re)s?|°\s*[cf]|celsius|fahrenheit)(?!\w)"
)
_NEGATION_PATTERN = re.compile(
    r"(?iu)(?<!\w)(?:not|no|never|without|cannot|can't|don't|doesn't|didn't|won't|"
    r"shouldn't|mustn't|\u0928\u0939\u0940\u0902|\u0928\u0939\u0940|\u092e\u0924|\u092c\u093f\u0928\u093e|"
    r"\u0c32\u0c47\u0c26\u0c41|\u0c15\u0c3e\u0c26\u0c41|\u0c35\u0c26\u0c4d\u0c26\u0c41|"
    r"\u0c32\u0c47\u0c15\u0c41\u0c02\u0c21\u0c3e)(?!\w)"
)
_PHONE_CONTEXT_PATTERN = re.compile(
    r"(?iu)(?<!\w)(?:phone|mobile|telephone|contact|call|number|"
    r"\u092b\u094b\u0928|\u092b\u094b\u0928|\u092e\u094b\u092c\u093e\u0907\u0932|\u0928\u0902\u092c\u0930|"
    r"\u0c2b\u0c4b\u0c28|\u0c2e\u0c4b\u0c2c\u0c48\u0c32|\u0c28\u0c02\u0c2c\u0c30)(?!\w)"
)
_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7,
    "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
    "जनवरी": 1, "फरवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5, "जून": 6,
    "जुलाई": 7, "अगस्त": 8, "सितंबर": 9, "अक्टूबर": 10, "नवंबर": 11, "दिसंबर": 12,
}
_RELATIVE_DATES = {
    "today": ("relative:today", False), "आज": ("relative:today", False),
    "tomorrow": ("relative:tomorrow", False), "रేపు": ("relative:tomorrow", False),
    "yesterday": ("relative:yesterday", False), "నిన్న": ("relative:yesterday", False),
    # Hindi kal means either yesterday or tomorrow without context.
    "कल": ("relative:kal", True),
    "परसों": ("relative:parson", True),
}


def _amounts(text: str) -> list[CriticalEntity]:
    entities: list[CriticalEntity] = []
    cursor = 0
    while cursor < len(text):
        parsed = parse_number(text[cursor:])
        if parsed is None:
            break
        local_start = text[cursor:].find(parsed.source_span)
        if local_start < 0:
            break
        start = cursor + local_start
        end = start + len(parsed.source_span)
        span = parsed.source_span
        folded = span.casefold()
        is_amount = parsed.is_currency or any(hint in folded for hint in (*_CURRENCY_HINTS, *_SCALE_HINTS))
        if is_amount:
            alternatives = ",".join(str(value) for value in parsed.alternatives)
            entities.append(
                CriticalEntity(
                    kind="amount",
                    normalized_value=format(parsed.normalized_value.normalize(), "f"),
                    source_span=span,
                    formatted=parsed.formatted,
                    needs_confirmation=parsed.needs_confirmation,
                    mapping_status=parsed.mapping_status,
                )
            )
        cursor = max(end, cursor + 1)
    return entities


def _numeric_mentions(text: str) -> list[tuple[int, int, object]]:
    """Locate all number expressions supported by the deterministic parser."""
    mentions = []
    cursor = 0
    while cursor < len(text):
        parsed = parse_number(text[cursor:])
        if parsed is None:
            break
        local_start = text[cursor:].find(parsed.source_span)
        if local_start < 0:
            cursor += 1
            continue
        start = cursor + local_start
        end = start + len(parsed.source_span)
        if parsed.source_span.casefold() not in {"a", "an"}:
            mentions.append((start, end, parsed))
        cursor = max(end, cursor + 1)
    return mentions


def _positions(text: str, entities: list[CriticalEntity]) -> list[tuple[int, int]]:
    positions = []
    cursors: dict[str, int] = {}
    for entity in entities:
        span = entity.source_span
        start = text.find(span, cursors.get(span, 0))
        if start >= 0:
            end = start + len(span)
            positions.append((start, end))
            cursors[span] = end
    return positions


def _overlaps(start: int, end: int, intervals: list[tuple[int, int]]) -> bool:
    return any(left < end and start < right for left, right in intervals)


def _percentages(text: str, mentions: list[tuple[int, int, object]]) -> list[CriticalEntity]:
    entities = []
    for marker in _PERCENT_MARKERS.finditer(text):
        number = next((item for item in reversed(mentions)
                       if item[1] <= marker.start() and not text[item[1]:marker.start()].strip(" \t,.-")), None)
        if number is None:
            continue
        start, _, parsed = number
        span = text[start:marker.end()]
        entities.append(CriticalEntity(
            "percentage", format(parsed.normalized_value.normalize(), "f"), span,
            f"{format(parsed.normalized_value.normalize(), 'f')}%",
            parsed.needs_confirmation, parsed.mapping_status,
        ))
    return entities


def _measurements(text: str, mentions: list[tuple[int, int, object]]) -> list[CriticalEntity]:
    entities = []
    for unit in _UNIT_PATTERN.finditer(text):
        number = next((item for item in reversed(mentions)
                       if item[1] <= unit.start() and not text[item[1]:unit.start()].strip(" \t,.-")), None)
        if number is None:
            continue
        start, _, parsed = number
        raw_unit = unit.group(1).casefold().replace(" ", "")
        if raw_unit.startswith("°"):
            raw_unit = raw_unit[0] + raw_unit[-1]
        normalized = f"{format(parsed.normalized_value.normalize(), 'f')} { _UNIT_ALIASES[raw_unit] }"
        entities.append(CriticalEntity(
            "measurement", normalized, text[start:unit.end()], normalized,
            parsed.needs_confirmation, parsed.mapping_status,
        ))
    return entities


def _phone_numbers(text: str, excluded: list[tuple[int, int]]) -> list[CriticalEntity]:
    entities = []
    normalized_text = text.translate(_DIGITS)
    for match in re.finditer(r"(?<!\w)\+?[\d\s().-]{7,20}\d(?!\w)", normalized_text):
        if _overlaps(*match.span(), excluded):
            continue
        context_start = max(0, match.start() - 24)
        context_end = min(len(text), match.end() + 24)
        if not _PHONE_CONTEXT_PATTERN.search(text[context_start:context_end]):
            continue
        digits = "".join(character for character in match.group() if character.isdigit())
        if not 7 <= len(digits) <= 15:
            continue
        entities.append(CriticalEntity("phone_number", digits, text[match.start():match.end()], digits))
    return entities


def _numbers(
    text: str,
    mentions: list[tuple[int, int, object]],
    excluded: list[tuple[int, int]],
) -> list[CriticalEntity]:
    entities = []
    for start, end, parsed in mentions:
        if _overlaps(start, end, excluded):
            continue
        value = format(parsed.normalized_value.normalize(), "f")
        entities.append(CriticalEntity(
            "number", value, text[start:end], value,
            parsed.needs_confirmation, parsed.mapping_status,
        ))
    return entities


def _negations(text: str) -> list[CriticalEntity]:
    matches = list(_NEGATION_PATTERN.finditer(text))
    if not matches:
        return []
    # These marker lists are provisional. Requiring speaker confirmation for
    # any detected negation avoids claiming scope equivalence before native review.
    return [CriticalEntity("negation", "present", text[m.start():m.end()], m.group(), True, "provisional")
            for m in matches]


def _date_entities(text: str) -> list[CriticalEntity]:
    normalized = text.translate(_DIGITS)
    entities: list[CriticalEntity] = []
    occupied: list[tuple[int, int]] = []

    for match in re.finditer(r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)", normalized):
        year, month, day = map(int, match.groups())
        try:
            value = date(year, month, day).isoformat()
            entities.append(CriticalEntity("date", value, text[match.start():match.end()], value))
        except ValueError:
            entities.append(CriticalEntity("date", "invalid", text[match.start():match.end()], text[match.start():match.end()], True))
        occupied.append(match.span())

    for match in re.finditer(r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})(?!\d)", normalized):
        if any(a < match.end() and match.start() < b for a, b in occupied):
            continue
        first, second, year = map(int, match.groups())
        if year < 100:
            year += 2000
        # Indian day/month ordering is the default. If both orders are valid
        # and differ, preserve the uncertainty instead of guessing.
        try:
            value = date(year, second, first).isoformat()
            ambiguous = first <= 12 and second <= 12 and first != second
        except ValueError:
            value, ambiguous = "invalid", True
        entities.append(CriticalEntity("date", value, text[match.start():match.end()], value, ambiguous))
        occupied.append(match.span())

    month_pattern = "|".join(sorted(map(re.escape, _MONTHS), key=len, reverse=True))
    for pattern in (
        rf"(?iu)(?<!\w)(\d{{1,2}})\s+({month_pattern})\s+(\d{{4}})(?!\d)",
        rf"(?iu)(?<!\w)({month_pattern})\s+(\d{{1,2}}),?\s+(\d{{4}})(?!\d)",
    ):
        for match in re.finditer(pattern, normalized):
            if any(a < match.end() and match.start() < b for a, b in occupied):
                continue
            groups = match.groups()
            if groups[0].isdigit():
                day, month_name, year = int(groups[0]), groups[1], int(groups[2])
            else:
                month_name, day, year = groups[0], int(groups[1]), int(groups[2])
            month = _MONTHS.get(month_name.casefold(), _MONTHS.get(month_name))
            try:
                value = date(year, month, day).isoformat()
                ambiguous = False
            except (TypeError, ValueError):
                value, ambiguous = "invalid", True
            entities.append(CriticalEntity("date", value, text[match.start():match.end()], value, ambiguous))
            occupied.append(match.span())

    for match in re.finditer(r"(?iu)(?<!\w)(today|tomorrow|yesterday|कल|आज|రేపు|నిన్న|परसों)(?!\w)", text):
        value, ambiguous = _RELATIVE_DATES[match.group(1).casefold()]
        entities.append(CriticalEntity("date", value, match.group(1), value, ambiguous))
    return entities


def _time_entities(text: str) -> list[CriticalEntity]:
    normalized = text.translate(_DIGITS)
    entities: list[CriticalEntity] = []
    occupied: list[tuple[int, int]] = []
    for date_match in re.finditer(r"(?<!\d)(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})(?!\d)", normalized):
        occupied.append(date_match.span())
    pattern = re.compile(r"(?iu)(?<!\d)(\d{1,2})(?::([0-5]\d))?\s*(am|pm)?(?!\w)")
    for match in pattern.finditer(normalized):
        if any(a < match.end() and match.start() < b for a, b in occupied):
            continue
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        marker = (match.group(3) or "").casefold()
        if not match.group(2) and not marker:
            continue
        if hour > 24 or (hour == 24 and minute != 0):
            continue
        if marker:
            if not 1 <= hour <= 12:
                continue
            hour = hour % 12 + (12 if marker == "pm" else 0)
        value = f"{hour:02d}:{minute:02d}"
        entities.append(CriticalEntity("time", value, text[match.start():match.end()], value))
        occupied.append(match.span())

    for marker in ("बजे", "గంటలకు", "గంటలకి", "గంటకు"):
        cursor = 0
        while (found := text.find(marker, cursor)) >= 0:
            left = max(text.rfind(" ", 0, found - 1), found - 32) + 1
            phrase = text[left:found]
            parsed = parse_number(phrase)
            if parsed and Decimal(0) <= parsed.normalized_value <= Decimal(24):
                hour = int(parsed.normalized_value)
                prefix = phrase.casefold()
                if any(word in prefix for word in ("दोपहर", "शाम", "సాయంత్రం")) and hour < 12:
                    hour += 12
                value = f"{hour:02d}:00"
                entities.append(CriticalEntity("time", value, text[left:found + len(marker)], value, parsed.needs_confirmation, parsed.mapping_status))
                occupied.append((left, found + len(marker)))
            cursor = found + len(marker)

    # Remove numeric clock captures inside a date.
    return [entity for entity in entities if entity.kind == "time"]


def extract_critical_entities(text: str) -> dict[str, list[dict]]:
    """Return supported deterministic critical-entity records from a transcript."""
    if not text:
        return {"amounts": [], "dates": [], "times": [], "percentages": [],
                "measurements": [], "phone_numbers": [], "numbers": [], "negations": []}
    amounts = _amounts(text)
    dates = _date_entities(text)
    times = _time_entities(text)
    mentions = _numeric_mentions(text)
    percentages = _percentages(text, mentions)
    measurements = _measurements(text, mentions)
    excluded = _positions(text, amounts + dates + times + percentages + measurements)
    phone_numbers = _phone_numbers(text, excluded)
    numbers = _numbers(text, mentions, excluded + _positions(text, phone_numbers))
    negations = _negations(text)
    return {
        "amounts": [item.to_dict() for item in amounts],
        "dates": [item.to_dict() for item in dates],
        "times": [item.to_dict() for item in times],
        "percentages": [item.to_dict() for item in percentages],
        "measurements": [item.to_dict() for item in measurements],
        "phone_numbers": [item.to_dict() for item in phone_numbers],
        "numbers": [item.to_dict() for item in numbers],
        "negations": [item.to_dict() for item in negations],
    }
