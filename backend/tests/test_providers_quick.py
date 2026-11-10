"""Quick sanity tests - runs directly without pytest."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.stt.mock import MockSttProvider
from app.services.tts.mock import MockTtsProvider
from app.services.translation.mock import MockTranslationProvider

passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1


async def main():
    print("--- STT Tests ---")
    stt = MockSttProvider()
    r = await stt.transcribe(b"x" * 1000, "hi")
    check("Hindi STT returns text", bool(r.text))
    check("Hindi STT language correct", r.language == "hi")
    check("Hindi STT has confidence", r.confidence is not None and r.confidence > 0)

    r2 = await stt.transcribe(b"x" * 1000, "te")
    check("Telugu STT returns text", bool(r2.text))
    check("Telugu STT language correct", r2.language == "te")

    r3 = await stt.transcribe(b"x" * 10, "hi")
    check("Short audio is_empty", r3.is_empty)

    print("\n--- Translation Tests ---")
    trans = MockTranslationProvider()
    t1 = await trans.translate("नमस्ते, मैं ठीक हूँ", "hi", "te")
    check("Hi->Te known phrase", t1.translated_text == "నమస్కారం, నేను బాగున్నాను")

    t2 = await trans.translate("सवा लाख रुपये भेज दीजिए", "hi", "te")
    check("Hi->Te sava lakh", "లక్ష ఇరవై ఐదు వేల" in (t2.translated_text or ""))

    t3 = await trans.translate("నమస్కారం, నేను బాగున్నాను", "te", "hi")
    check("Te->Hi known phrase", t3.translated_text == "नमस्ते, मैं ठीक हूँ")

    t4 = await trans.translate("random text", "hi", "te")
    check("Fallback has [Mock]", t4.translated_text.startswith("[Mock"))

    print("\n--- TTS Tests ---")
    tts = MockTtsProvider()
    tts_r = await tts.synthesize("test text", "hi")
    check("TTS returns bytes", len(tts_r.audio_bytes) > 44)
    check("TTS is valid WAV", tts_r.audio_bytes[:4] == b"RIFF")
    check("TTS format is wav", tts_r.audio_format == "wav")

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASSED!")
    else:
        sys.exit(1)


asyncio.run(main())
