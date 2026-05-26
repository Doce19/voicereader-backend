import os
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)

OUTPUT_DIR = "audio_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

GTTS_LANG = {
    "fr": "fr",
    "en": "en",
}

def text_to_speech(text: str, document_id: int, lang: str = "fr", genre: str = "feminin") -> str:
    output_path = os.path.join(OUTPUT_DIR, f"document_{document_id}.mp3")

    if not text or not text.strip():
        raise ValueError("Aucun texte disponible pour générer l'audio.")

    gtts_lang = GTTS_LANG.get(lang, "fr")

    try:
        tts = gTTS(
            text=text,
            lang=gtts_lang,
            slow=False,
        )
        tts.save(output_path)
        logger.info(f"gTTS success: {output_path}")
        return output_path

    except Exception as e:
        logger.exception(f"gTTS failed: {e}")
        raise