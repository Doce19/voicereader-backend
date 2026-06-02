import os
import logging
import asyncio
import edge_tts
import json

logger = logging.getLogger(__name__)

OUTPUT_DIR = "audio_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration des voix de qualité supérieure de Microsoft
VOICES = {
    "fr": {
        "feminin": "fr-FR-DeniseNeural",
        "masculin": "fr-FR-HenriNeural"
    },
    "en": {
        "feminin": "en-US-EmmaNeural",
        "masculin": "en-US-BrianNeural"
    }
}

async def text_to_speech_edge(text: str, document_id: int, lang: str = "fr", genre: str = "feminin"):
    """
    Génère le fichier MP3 et un fichier JSON contenant les timestamps exacts de chaque mot.
    """
    base_name = f"document_{document_id}"
    audio_path = os.path.join(OUTPUT_DIR, f"{base_name}.mp3")
    json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")

    if not text or not text.strip():
        raise ValueError("Aucun texte disponible pour générer l'audio.")

    # Sélection de la voix ou repli sur Denise (Français Féminin) par défaut
    voice = VOICES.get(lang, VOICES["fr"]).get(genre, VOICES["fr"]["feminin"])
    
    logger.info(f"Démarrage génération Edge-TTS avec la voix : {voice}")

    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()

    try:
        # On extrait les données audio et les marqueurs temporels en même temps
        with open(audio_path, "wb") as fp:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    fp.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # submaker enregistre la position exacte de chaque mot
                    submaker.feed(chunk)

        # CORRECTION ICI : Extraction propre des sous-titres/timestamps depuis les indices internes de SubMaker
        timestamps = []
        for start, end, word in submaker.cues:
            timestamps.append({
                "word": word,
                "start": start.total_seconds(),
                "end": end.total_seconds()
            })

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(timestamps, jf, ensure_ascii=False, indent=2)

        logger.info(f"Edge-TTS succès : {audio_path} et {json_path}")
        return audio_path, json_path

    except Exception as e:
        logger.exception(f"Edge-TTS échec : {e}")
        raise