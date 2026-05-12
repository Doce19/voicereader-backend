import os
import asyncio
import edge_tts

OUTPUT_DIR = "audio_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VOICES = {
    "fr": {
        "masculin": "fr-FR-HenriNeural",
        "feminin": "fr-FR-DeniseNeural"
    },
    "en": {
        "masculin": "en-US-GuyNeural",
        "feminin": "en-US-JennyNeural"
    }
}

async def generate_audio(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

def text_to_speech(text: str, document_id: int, lang: str = "fr", genre: str = "feminin") -> str:
    output_path = os.path.join(OUTPUT_DIR, f"document_{document_id}.mp3")
    voice = VOICES.get(lang, VOICES["fr"]).get(genre, "fr-FR-DeniseNeural")
    asyncio.run(generate_audio(text, voice, output_path))
    return output_path