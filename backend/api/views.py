from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
import os
from api.speech_to_text import get_transcript


class UploadVideoView(APIView):
    parser_classes = [MultiPartParser]  # Allows file uploads

    def post(self, request, *args, **kwargs):
        video = request.FILES.get("video")

        if not video:
            return Response({"error": "No video uploaded"}, status=400)

        # Save the video temporarily
        video_path = f"media/{video.name}"
        os.makedirs("media", exist_ok=True)  # Ensure media directory exists
        with open(video_path, "wb+") as f:
            for chunk in video.chunks():
                f.write(chunk)

        # Get transcript using your speech_to_text function
        transcript = get_transcript(video_path)

        # Clean up temporary file
        if os.path.exists(video_path):
            os.remove(video_path)

        # Check if transcription failed
        if transcript.startswith("Error:"):
            return Response({"error": transcript}, status=500)

        return Response({"transcript": transcript}, status=200)  # ✅ Fixed typo
