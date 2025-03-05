import subprocess
import whisper

# extracts ONLY the audio from the video file


def extract_audio(video_path, audio_path="output_audio.mp3"):
    command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3", audio_path]
    subprocess.run(command, check=True)
    return audio_path


# converts the audio file into actual text
def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)
    return result


# formatting the time into mins and secs
def format_time(seconds):
    minutes = int(seconds//60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"


# puts everything into a nice .txt file
def save_transcript(transcription, output_file="transcript.txt"):
    with open(output_file, 'w') as f:
        for segment in transcription["segments"]:
            start = format_time(segment['start'])
            end = format_time(segment["end"])
            text = segment["text"]
            f.write(f"[{start} - {end}] {text}\n")

            print(f"Transcript saved as: {output_file}")


# Run the script
video_file = "public/nia (1).mp4"
audio_file = extract_audio(video_file)
transcription = transcribe_audio(audio_file)
save_transcript(transcription)



# just a test