import subprocess
import os
from pathlib import Path
import logging
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_audio(video_path: str, audio_path: str = "output_audio.mp3") -> str | None:
    """Extract audio from video file using ffmpeg if needed."""
    try:
        # Check if the file is already in a supported audio format
        supported_audio_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        file_ext = os.path.splitext(video_path)[1].lower()
        
        # Get file size in MB
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        logger.info(f"Processing file: {video_path} ({file_size_mb:.2f} MB)")
        
        # If file is small and already in supported format, just return it
        if file_ext in supported_audio_formats and file_size_mb < 25:  # OpenAI has 25MB limit
            logger.info(f"File is already in supported format ({file_ext}) and under size limit. Skipping conversion.")
            return video_path
            
        # Otherwise, extract audio to reduce size
        logger.info(f"Converting video to audio format using ffmpeg")
        command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3", audio_path]
        subprocess.run(command, check=True)
        return audio_path
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return None

def transcribe_audio(audio_path: str) -> dict:
    """Transcribe audio using OpenAI's Whisper API with timestamps."""
    try:
        client = OpenAI()

        with open(audio_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Error transcribing audio with OpenAI API: {e}")
        return None

def format_time(seconds: float) -> str:
    """Format time in seconds to MM:SS.ss format."""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"

def get_transcript(video_path: str) -> str:
    """Process video file and return transcript with timestamps using OpenAI's API."""
    # Create media directory if it doesn't exist
    media_dir = Path("media")
    media_dir.mkdir(exist_ok=True)
    
    # Generate unique audio file path for potential conversion
    audio_path = media_dir / "output_audio.mp3"
    
    # Extract audio if needed (may return original file if it's already in the right format)
    audio_file = extract_audio(video_path, str(audio_path))
    if not audio_file:
        return "Error: Could not process audio."

    # Transcribe audio using OpenAI API
    result = transcribe_audio(audio_file)
    if not result:
        return "Error: Could not transcribe audio."
    
    # Clean up temporary files
    # Only remove audio_file if it's different from the video_path (means we created a new file)
    if os.path.exists(audio_file) and audio_file != video_path:
        logger.info(f"Removing temporary audio file: {audio_file}")
        os.remove(audio_file)
        
    # Always remove the original video file when we're done
    if os.path.exists(video_path):
        logger.info(f"Removing original video file: {video_path}")
        os.remove(video_path)

    # Return the OpenAI response as JSON
    try:
        import json
        
        # Convert the API response to a dictionary
        if hasattr(result, 'model_dump'):
            # If it's a Pydantic model or similar
            result_dict = result.model_dump()
        elif hasattr(result, '__dict__'):
            # If it's an object with __dict__
            result_dict = result.__dict__
        elif isinstance(result, dict):
            # If it's already a dict
            result_dict = result
        else:
            # Otherwise, convert to string
            return str(result)
        
        # Log the structure we're returning
        logger.info(f"Returning transcript with {len(result_dict.get('segments', []))} segments")
        
        return json.dumps(result_dict)
    except Exception as e:
        logger.error(f"Error serializing result to JSON: {e}")
        return str(result)

def save_transcript(transcript_text: str, output_file: str = "transcript.txt") -> None:
    """Save transcript to a file."""
    with open(output_file, "w") as f:
        f.write(transcript_text)
    logger.info(f"Transcript saved as: {output_file}") 