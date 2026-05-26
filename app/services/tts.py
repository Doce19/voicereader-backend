from gtts import gTTS

def text_to_speech(text: str, output_path: str, lang: str = "fr", genre: str = "feminin"):
    if not text or not text.strip():
        raise ValueError("Aucun texte à convertir en audio.")

    lang_code = "fr" if lang == "fr" else "en"

    tts = gTTS(
        text=text,
        lang=lang_code,
        slow=False
    )

    tts.save(output_path)
    return output_path