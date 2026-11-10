import pytest
from app.main import SUPPORTED_LANGUAGES, ParticipantRequest
from app.services.stt.gnani import GnaniPrismaProvider
from app.services.tts.gnani import GnaniTimbreProvider, LANGUAGE_CODES, DEFAULT_VOICES
from app.services.translation.gemini_translate import LANG_NAMES


def test_supported_languages_count():
    assert len(SUPPORTED_LANGUAGES) >= 12
    assert "en" in SUPPORTED_LANGUAGES
    assert "hi" in SUPPORTED_LANGUAGES
    assert "te" in SUPPORTED_LANGUAGES
    assert "ta" in SUPPORTED_LANGUAGES
    assert "kn" in SUPPORTED_LANGUAGES
    assert "ml" in SUPPORTED_LANGUAGES
    assert "mr" in SUPPORTED_LANGUAGES
    assert "bn" in SUPPORTED_LANGUAGES
    assert "gu" in SUPPORTED_LANGUAGES
    assert "pa" in SUPPORTED_LANGUAGES
    assert "or" in SUPPORTED_LANGUAGES
    assert "ur" in SUPPORTED_LANGUAGES


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGUAGES))
def test_participant_request_accepts_all_supported_languages(lang):
    req = ParticipantRequest(participant_name="User", language=lang)
    assert req.language == lang


def test_participant_request_rejects_invalid_language():
    with pytest.raises(ValueError):
        ParticipantRequest(participant_name="User", language="fr")


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGUAGES))
def test_gnani_timbre_supports_all_languages(lang):
    provider = GnaniTimbreProvider("test_key", "https://api.vachana.ai/api/v1/tts/inference")
    assert lang in LANGUAGE_CODES
    assert lang in DEFAULT_VOICES


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGUAGES))
def test_gemini_translation_has_human_name(lang):
    assert lang in LANG_NAMES
    assert isinstance(LANG_NAMES[lang], str)
