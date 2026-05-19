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

def split_text(text: str, chunk_size: int = 1000) -> list:
    sentences = text.replace('\n', ' ').split('. ')
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) < chunk_size:
            current += sentence + ". "
        else:
            if current:
                chunks.append(current.strip())
            current = sentence + ". "
    if current:
        chunks.append(current.strip())
    return chunks

async def generate_chunk(text: str, voice: str, path: str):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(path)

async def generate_full_audio(text: str, voice: str, output_path: str):
    chunks = split_text(text)
    chunk_paths = []

    for i, chunk in enumerate(chunks):
        chunk_path = output_path.replace('.mp3', f'_chunk_{i}.mp3')
        await generate_chunk(chunk, voice, chunk_path)
        chunk_paths.append(chunk_path)

    # Combine tous les chunks en un seul fichier
    with open(output_path, 'wb') as outfile:
        for chunk_path in chunk_paths:
            with open(chunk_path, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(chunk_path)

def text_to_speech(text: str, document_id: int, lang: str = "fr", genre: str = "feminin") -> str:
    output_path = os.path.join(OUTPUT_DIR, f"document_{document_id}.mp3")
    voice = VOICES.get(lang, VOICES["fr"]).get(genre, "fr-FR-DeniseNeural")
    asyncio.run(generate_full_audio(text, voice, output_path))
    return output_path