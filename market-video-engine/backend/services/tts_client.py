"""Text-to-speech helper using gTTS with speed control."""

from __future__ import annotations

import os
import subprocess
import tempfile

from gtts import gTTS


# Speed multiplier: 1.25 = 25% faster narration pace
TTS_SPEED = 1.25


def _speed_up_audio(input_path: str, speed: float) -> str:
    """Uses ffmpeg atempo filter to speed up audio without pitch shift."""
    if speed == 1.0:
        return input_path

    output_path = input_path.replace(".mp3", "_fast.mp3")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-filter:a", f"atempo={speed}",
                "-vn", output_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            os.remove(input_path)
            return output_path
    except Exception:
        pass
    return input_path


def generate_audio(script: str, lang: str = "en") -> str | None:
    """Converts text to MP3 at 1.25x speed and returns the file path.

    Returns None if TTS fails so the pipeline can continue without audio.
    """
    if not script.strip():
        return None

    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()

        tts = gTTS(text=script, lang=lang, slow=False)
        tts.save(tmp_path)

        # Speed up to 1.25x for tighter pacing
        tmp_path = _speed_up_audio(tmp_path, TTS_SPEED)

        return tmp_path
    except Exception:
        return None
