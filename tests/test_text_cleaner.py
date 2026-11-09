"""Unit test suite for text normalization, multilingual video routes, and multilingual AI synthesis."""

import pytest
from app.services.text_cleaner import (
    TextCleaner,
    normalize_text_for_tts,
    normalize_identifier,
    strip_file_extensions,
    remove_syntax_symbols,
    split_technical_identifiers,
    parse_script_into_scenes,
)
from app.schemas.video_schemas import (
    SUPPORTED_LANGUAGES,
    resolve_language_info,
    GenerateVideoRequest,
    GenerateVideoResponse,
    LanguageInfo,
)
from app.services.gemini_service import GeminiScriptService
from app.services.tts_service import TTSOptions, TTSService, ScriptCleaner


# =============================================================================
# 1. Identifier & Code Normalization Tests
# =============================================================================


def test_snake_case_normalization():
    assert normalize_identifier("auth_middleware") == "auth middleware"
    assert normalize_identifier("order_processing_service") == "order processing service"
    assert normalize_identifier("get_user_by_id") == "get user by id"
    assert normalize_identifier("__init__") == "init"


def test_camel_and_pascal_case_normalization():
    assert normalize_identifier("OrderProcessor") == "Order Processor"
    assert normalize_identifier("getUserById") == "get User By Id"
    assert normalize_identifier("HTTPServer") == "HTTP Server"
    assert normalize_identifier("APIClientGateway") == "API Client Gateway"


def test_strip_file_extensions():
    text = "Inspect app/routes/user.py and components/Button.tsx or settings.json and schema.sql"
    cleaned = strip_file_extensions(text)
    assert ".py" not in cleaned
    assert ".tsx" not in cleaned
    assert ".json" not in cleaned
    assert ".sql" not in cleaned
    assert "user" in cleaned
    assert "Button" in cleaned


def test_syntax_symbols_removal():
    raw = "def process(item: Dict[str, Any]) -> bool: { return True; } != =="
    cleaned = remove_syntax_symbols(raw)
    for sym in ["{", "}", "[", "]", "(", ")", ";", "->", "==", "!="]:
        assert sym not in cleaned


def test_unicode_preservation_in_text_cleaning():
    # Gujarati
    gujarati_text = "આ auth_middleware.py ફાઈલ વિનંતીઓ પ્રમાણિત કરે છે."
    cleaned_gu = normalize_text_for_tts(gujarati_text, language="gu")
    assert "આ" in cleaned_gu
    assert "વિનંતીઓ" in cleaned_gu
    assert "પ્રમાણિત" in cleaned_gu
    assert "auth middleware" in cleaned_gu
    assert ".py" not in cleaned_gu

    # Hindi
    hindi_text = "यह order_service.py डेटाबेस मॉडल्स को संभालता है।"
    cleaned_hi = normalize_text_for_tts(hindi_text, language="hi")
    assert "यह" in cleaned_hi
    assert "डेटाबेस" in cleaned_hi
    assert "order service" in cleaned_hi
    assert ".py" not in cleaned_hi

    # Spanish
    spanish_text = "El módulo auth_controller.ts gestiona la autenticación segura."
    cleaned_es = normalize_text_for_tts(spanish_text, language="es")
    assert "autenticación" in cleaned_es
    assert "auth controller" in cleaned_es
    assert ".ts" not in cleaned_es


# =============================================================================
# 2. Scene Parser Tests
# =============================================================================


def test_parse_script_into_scenes():
    script = """
    [Scene 1: Introduction & File Tree]
    Welcome to helper-AI. The order_service.py coordinates requests.
    
    [Scene 2: Architecture Topology]
    Requests pass through the auth_middleware and hit PostgreSQL.
    """
    scenes = parse_script_into_scenes(script)
    assert len(scenes) == 2
    assert "scene_1" in scenes[0]["scene_id"]
    assert "order service" in scenes[0]["text"]
    assert "scene_2" in scenes[1]["scene_id"]
    assert "auth middleware" in scenes[1]["text"]


# =============================================================================
# 3. Multilingual Catalog & Schema Resolution Tests
# =============================================================================


def test_supported_languages_catalog():
    # Verify all major Indian languages are present
    indian_codes = ["gu", "hi", "mr", "bn", "ta", "te", "kn", "ml", "pa", "ur"]
    for code in indian_codes:
        assert code in SUPPORTED_LANGUAGES
        info = SUPPORTED_LANGUAGES[code]
        assert info.name
        assert info.native_name
        assert info.default_voice.startswith(code) or "Neural" in info.default_voice

    # Verify world languages
    world_codes = ["es", "fr", "de", "ja", "zh", "ar", "en"]
    for code in world_codes:
        assert code in SUPPORTED_LANGUAGES


def test_resolve_language_info():
    # Exact code
    gu = resolve_language_info("gu")
    assert gu.code == "gu"
    assert gu.name == "Gujarati"
    assert "Dhwani" in gu.default_voice

    # Case insensitivity & whitespace
    hi = resolve_language_info("  HI  ")
    assert hi.code == "hi"
    assert hi.name == "Hindi"

    # Match by name
    french = resolve_language_info("French")
    assert french.code == "fr"

    # Fallback to English for unknown
    unknown = resolve_language_info("klingon")
    assert unknown.code == "en"
    assert unknown.name == "English"


def test_generate_video_request_schema():
    # Default target_language is en
    req_default = GenerateVideoRequest(repo_url="owner/repo")
    assert req_default.target_language == "en"

    # Custom Indian language
    req_gu = GenerateVideoRequest(repo_url="owner/repo", target_language="gu")
    assert req_gu.target_language == "gu"

    # Custom World language
    req_es = GenerateVideoRequest(repo_url="owner/repo", target_language="es")
    assert req_es.target_language == "es"


# =============================================================================
# 4. Multilingual AI Synthesis Tests (Gemini Heuristic)
# =============================================================================


def test_gemini_multilingual_synthesis_gujarati():
    gemini_svc = GeminiScriptService()
    mock_pack = "## File: app/routes/auth.py\ndef login(): pass\n## File: app/models/user.py\nclass User: pass"
    res = gemini_svc.synthesize_script_and_architecture(
        codebase_pack=mock_pack,
        repo_name="demo-gu-repo",
        target_language="gu",
    )
    assert res.target_language == "gu"
    # Narration should contain Gujarati characters
    assert "આર્કિટેક્ચરલ" in res.narration_script or "વિશ્લેષણમાં" in res.narration_script
    assert "[Scene 1:" in res.narration_script


def test_gemini_multilingual_synthesis_hindi():
    gemini_svc = GeminiScriptService()
    mock_pack = "## File: app/server.py\ndef run(): pass\n## File: app/db.py\nclass Database: pass"
    res = gemini_svc.synthesize_script_and_architecture(
        codebase_pack=mock_pack,
        repo_name="demo-hi-repo",
        target_language="hi",
    )
    assert res.target_language == "hi"
    # Narration should contain Hindi characters
    assert "आर्किटेक्चरल" in res.narration_script or "विश्लेषण" in res.narration_script
    assert "[Scene 1:" in res.narration_script


def test_gemini_multilingual_synthesis_spanish():
    gemini_svc = GeminiScriptService()
    mock_pack = "## File: main.py\ndef start(): pass"
    res = gemini_svc.synthesize_script_and_architecture(
        codebase_pack=mock_pack,
        repo_name="demo-es-repo",
        target_language="es",
    )
    assert res.target_language == "es"
    assert "arquitectónico" in res.narration_script or "Bienvenidos" in res.narration_script


# =============================================================================
# 5. TTS Voice Auto-Resolution Tests
# =============================================================================


@pytest.mark.asyncio
async def test_tts_voice_auto_resolution(tmp_path):
    tts_svc = TTSService(workspace_dir=tmp_path)

    # When user passes Gujarati with default English voice, service auto-resolves to Dhwani
    opts = TTSOptions(language="gu", voice="en-US-ChristopherNeural")
    resolved_info = resolve_language_info(opts.language)
    assert resolved_info.default_voice == "gu-IN-DhwaniNeural"

    # When user passes Hindi, auto-resolves to Swara
    opts_hi = TTSOptions(language="hi")
    resolved_hi = resolve_language_info(opts_hi.language)
    assert resolved_hi.default_voice == "hi-IN-SwaraNeural"


def test_script_cleaner_integration_with_text_cleaner():
    raw_script = """
    [Scene 1: File Tree]
    Check out user_auth_service.py and database_connection_pool.ts!
    """
    cleaned = ScriptCleaner.clean_narration_text(raw_script, language="en")
    assert "user auth service" in cleaned
    assert "database connection pool" in cleaned
    assert ".py" not in cleaned
    assert ".ts" not in cleaned

