import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from app.ivr.constants import PromptKey, DEFAULT_LANGUAGE

_PROMPT_CACHE: Dict[str, Dict[str, str]] = {}


def load_prompts(language: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    """Loads prompt catalog for specified language with in-memory caching."""
    if language in _PROMPT_CACHE:
        return _PROMPT_CACHE[language]

    prompts_dir = Path(__file__).resolve().parent / "prompts"
    prompt_file = prompts_dir / f"{language}.json"

    if not prompt_file.exists():
        # Fallback to hi-IN
        prompt_file = prompts_dir / "hi-IN.json"

    if prompt_file.exists():
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                _PROMPT_CACHE[language] = data
                return data
        except Exception:
            pass

    return {}


class AudioCatalog:
    """
    Catalog providing stable prompt keys, fallback text, and audio mapping.
    In Phase 1 (Local Simulator), returns text and prompt keys.
    In future phases, maps prompt keys to pre-recorded audio files or TTS IDs.
    """

    @staticmethod
    def get_prompt_text(
        prompt_key: Union[PromptKey, str],
        language: str = DEFAULT_LANGUAGE,
        **format_kwargs: Any,
    ) -> str:
        key_str = (
            prompt_key.value if isinstance(prompt_key, PromptKey) else str(prompt_key)
        )
        prompts = load_prompts(language)
        raw_text = prompts.get(key_str, f"Prompt: {key_str}")

        if format_kwargs:
            try:
                return raw_text.format(**format_kwargs)
            except KeyError:
                return raw_text
        return raw_text

    @staticmethod
    def get_audio_asset_id(
        prompt_key: Union[PromptKey, str], language: str = DEFAULT_LANGUAGE
    ) -> Optional[str]:
        """
        Placeholder mapping for pre-recorded audio assets in Phase 2.
        Returns None for Phase 1 local simulator.
        """
        # Placeholder for future telephony phase: e.g. f"{language.lower().replace('-', '_')}_{key_str.lower()}.wav"
        _ = prompt_key
        _ = language
        return None
