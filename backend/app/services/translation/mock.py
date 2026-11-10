from app.services.translation.provider import TranslationProvider, TranslationResult

MOCK_TRANSLATIONS = {
    "hi_to_te": {
        "नमस्ते, मैं ठीक हूँ": "నమస్కారం, నేను బాగున్నాను",
        "सवा लाख रुपये भेज दीजिए": "లక్ష ఇరవై ఐదు వేల రూపాయలు పంపండి",
        "कल दोपहर दो बजे मिलते हैं": "రేపు మధ్యాహ్నం రెండు గంటలకు కలుద్దాం",
        "पचास हजार रुपये चाहिए": "యాభై వేల రూపాయలు కావాలి",
        "मुझे तीन किलो चावल चाहिए": "నాకు మూడు కిలోల బియ్యం కావాలి",
        "ढाई हजार रुपये दे दो": "రెండు వేల ఐదు వందల రూపాయలు ఇవ్వండి",
        "पौने दो लाख का सामान आया है": "లక్ష డెబ్బై ఐదు వేల సామాను వచ్చింది",
    },
    "te_to_hi": {
        "నమస్కారం, నేను బాగున్నాను": "नमस्ते, मैं ठीक हूँ",
        "లక్ష ఇరవై ఐదు వేల రూపాయలు పంపండి": "सवा लाख रुपये भेज दीजिए",
        "రేపు మధ్యాహ్నం రెండు గంటలకు కలుద్దాం": "कल दोपहर दो बजे मिलते हैं",
        "యాభై వేల రూపాయలు కావాలి": "पचास हजार रुपये चाहिए",
        "నాకు మూడు కిలోల బియ్యం కావాలి": "मुझे तीन किलो चावल चाहिए",
    },
}


class MockTranslationProvider(TranslationProvider):
    """Mock translation with pre-mapped Hindi-Telugu pairs."""

    async def translate(
        self, text: str, source_language: str, target_language: str
    ) -> TranslationResult:
        key = f"{source_language}_to_{target_language}"
        translations = MOCK_TRANSLATIONS.get(key, {})
        translated = translations.get(text, f"[Mock {target_language}] {text}")

        return TranslationResult(
            translated_text=translated,
            source_language=source_language,
            target_language=target_language,
        )
