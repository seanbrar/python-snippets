#!/usr/bin/env python3
import os
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

try:
    # Optional, only used if a .env file is present
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # type: ignore

try:
    # ElevenLabs SDK: pip install elevenlabs
    from elevenlabs.client import ElevenLabs  # type: ignore
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'elevenlabs'. Install with: pip install elevenlabs"
    ) from exc


MEDIA_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mpeg",
    ".mpg",
    ".3gp",
    ".m4a",
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".aac",
    ".wma",
}


def find_media_files(directory: Path) -> Iterable[Path]:
    for entry in sorted(directory.iterdir()):
        if entry.is_file() and entry.suffix.lower() in MEDIA_EXTENSIONS:
            yield entry


def read_file_bytes(file_path: Path) -> BytesIO:
    data = file_path.read_bytes()
    return BytesIO(data)


def extract_text_from_response(transcription: object) -> Optional[str]:
    # Works with dict-like or SDK model objects
    if hasattr(transcription, "text"):
        text_value = getattr(transcription, "text")
        if isinstance(text_value, str) and text_value.strip():
            return text_value

    if isinstance(transcription, dict):
        text_value = transcription.get("text")
        if isinstance(text_value, str) and text_value.strip():
            return text_value

        transcripts = transcription.get("transcripts")
        if isinstance(transcripts, list):
            pieces: list[str] = []
            for t in transcripts:
                if isinstance(t, dict):
                    t_text = t.get("text")
                else:
                    t_text = getattr(t, "text", None)
                if isinstance(t_text, str) and t_text.strip():
                    pieces.append(t_text)
            if pieces:
                return "\n\n".join(pieces)

    return None


def main() -> None:
    # Load .env if available
    if load_dotenv is not None:
        load_dotenv()  # no-op if no .env present

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise SystemExit(
            "ELEVENLABS_API_KEY is not set. Add it to your environment or a .env file."
        )

    # Base directory of this repository
    repo_root = Path(__file__).resolve().parent.parent
    media_dir = repo_root / "video-files"

    if not media_dir.exists():
        raise SystemExit(f"Directory not found: {media_dir}")

    media_files = list(find_media_files(media_dir))
    if not media_files:
        print(f"No supported media files found in {media_dir}")
        return

    client = ElevenLabs(api_key=api_key, base_url="https://api.elevenlabs.io")

    for media_path in media_files:
        output_path = media_path.with_suffix(media_path.suffix + ".transcript.txt")
        if output_path.exists():
            print(f"Skipping (exists): {output_path.name}")
            continue

        print(f"Transcribing: {media_path.name} …")
        audio_buffer = read_file_bytes(media_path)

        try:
            transcription = client.speech_to_text.convert(
                file=audio_buffer,
                model_id="scribe_v1",
                # Keep it simple and readable; set to None to auto-detect
                language_code="eng",
                diarize=False,
                tag_audio_events=False,
            )

            text = extract_text_from_response(transcription) or ""
            output_path.write_text(text, encoding="utf-8")
            print(f"Saved: {output_path.name}")
        except Exception as exc:
            print(f"Failed: {media_path.name}: {exc}")


if __name__ == "__main__":
    main()
