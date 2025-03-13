import subprocess
import whisper


def extract_audio(video_path, audio_path="output_audio.mp3"):
    try:
        command = ["ffmpeg", "-i", video_path,
                   "-vn", "-acodec", "mp3", audio_path]
        subprocess.run(command, check=True)
        return audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None  # Handle failure gracefully


def transcribe_audio(audio_path):
    try:
        model = whisper.load_model("base")
        print("Whisper model loaded successfully!")

        result = model.transcribe(audio_path, word_timestamps=True)
        return result
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None


# Formatting the time into minutes and seconds
def format_time(seconds):
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"


def get_transcript(video_path):
    audio_file = extract_audio(video_path)
    if not audio_file:
        return "Error: Could not extract audio."

    transcription = transcribe_audio(audio_file)
    if not transcription:
        return "Error: Could not transcribe audio."

    transcript_data = []
    for segment in transcription["segments"]:
        start = format_time(segment['start'])
        end = format_time(segment["end"])
        text = segment["text"]

        # ✅ Store as JSON-friendly format
        transcript_data.append({
            "start_time": start,
            "end_time": end,
            "text": text
        })

    print('THE TRANSCRIPT WORKED!')
    return transcript_data  # ✅ Returns structured JSON


def save_transcript(transcript_text, output_file="transcript.txt"):
    with open(output_file, "w") as f:
        f.write(transcript_text)
    print(f"Transcript saved as: {output_file}")
