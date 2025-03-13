import requests
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from api.speech_to_text import get_transcript


class UploadVideoView(APIView):

    def post(self, request, *args, **kwargs):
        video = request.FILES.get("video")

        if not video:
            return Response({"error": "No video uploaded"}, status=400)

        video_path = f"media/{video.name}"
        with open(video_path, "wb") as f:
            for chunk in video.chunks():
                f.write(chunk)

        transcript = get_transcript(video_path)

        if os.path.exists(video_path):
            os.remove(video_path)

        if isinstance(transcript, str) and transcript.startswith("Error:"):
            return Response({"error": transcript}, status=500)

        # ✅ Correct FastAPI request structure
        fastapi_url = "http://localhost:8001/api/chat/structured"
        payload = {
            "request": {  # ✅ Wrap inside "request" key
                "message": transcript,
                "conversation_id": None
            }
        }

        headers = {"Content-Type": "application/json"}

        try:
            print("🔥 Sending request to FastAPI endpoint:", fastapi_url)
            fastapi_response = requests.post(
                fastapi_url, json=payload, headers=headers)

            print("🚀 FastAPI status code:", fastapi_response.status_code)
            print("📦 FastAPI response:", fastapi_response.text)

            fastapi_response.raise_for_status()  # ✅ Catch HTTP errors clearly

            feedback_data = fastapi_response.json()

        except requests.RequestException as e:
            print("❌ Exception occurred:", e)
            return Response({"error": f"FastAPI connection error: {str(e)}"}, status=500)

        return Response({
            "transcript": transcript,
            "structured_feedback": feedback_data["response"]
        }, status=200)
