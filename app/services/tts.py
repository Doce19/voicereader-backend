import os
import asyncio
import edge_tts
from gtts import gTTS
import logging

logger = logging.getLogger(__name__)
OUTPUT_DIR = "audio_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VOICES = {
    "fr": {"masculin": "fr-FR-HenriNeural", "feminin": "fr-FR-DeniseNeural"},
    "en": {"masculin": "en-US-GuyNeural", "feminin": "en-US-JennyNeural"}
}

GTTS_LANG = {"fr": "fr", "en": "en"}

async def generate_edge(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

def text_to_speech(text: str, document_id: int, lang: str = "fr", genre: str = "feminin") -> str:
    output_path = os.path.join(OUTPUT_DIR, f"document_{document_id}.mp3")
    voice = VOICES.get(lang, VOICES["fr"]).get(genre, "fr-FR-DeniseNeural")
    
    try:
        asyncio.run(generate_edge(text, voice, output_path))
        logger.info("Edge TTS success")
        return output_path
    except Exception as e:
        logger.warning(f"Edge TTS failed: {e} - Falling back to gTTS")
        gtts_lang = GTTS_LANG.get(lang, "fr")
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(output_path)
        logger.info("gTTS fallback success")
        return output_path