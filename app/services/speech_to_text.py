import subprocess
import whisper
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_audio(video_path: str, audio_path: str = "output_audio.mp3") -> str | None:
    """Extract audio from video file using ffmpeg."""
    try:
        command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3", audio_path]
        subprocess.run(command, check=True)
        return audio_path
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return None

def transcribe_audio(audio_path: str) -> dict | None:
    """Transcribe audio using Whisper model."""
    try:
        model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully!")

        result = model.transcribe(audio_path, word_timestamps=True)
        return result
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None

def format_time(seconds: float) -> str:
    """Format time in seconds to MM:SS.ss format."""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"

def get_transcript(video_path: str) -> str:
    """Process video file and return formatted transcript."""
    # Create media directory if it doesn't exist
    media_dir = Path("media")
    media_dir.mkdir(exist_ok=True)
    
    # Generate unique audio file path
    audio_path = media_dir / "output_audio.mp3"
    
    # Extract and transcribe audio
    audio_file = extract_audio(video_path, str(audio_path))
    if not audio_file:
        return "Error: Could not extract audio."

    transcription = transcribe_audio(audio_file)
    if not transcription:
        return "Error: Could not transcribe audio."

    # Format transcript
    transcript_lines = []
    for segment in transcription["segments"]:
        start = format_time(segment['start'])
        end = format_time(segment["end"])
        text = segment["text"]
        transcript_lines.append(f"[{start} - {end}] {text}")

    # Remove the first line if it exists (often contains noise)
    if transcript_lines:
        transcript_lines.pop(0)

    # Clean up temporary files
    if os.path.exists(audio_file):
        os.remove(audio_file)
    if os.path.exists(video_path):
        os.remove(video_path)

    return "\n".join(transcript_lines)

def save_transcript(transcript_text: str, output_file: str = "transcript.txt") -> None:
    """Save transcript to a file."""
    with open(output_file, "w") as f:
        f.write(transcript_text)
    logger.info(f"Transcript saved as: {output_file}") 