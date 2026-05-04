from django.shortcuts import render
from . import services
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework import status
from .serializers import ChatMessageSerializer, ChatSessionSerializer, ChatInputSerializer 

class ChatSessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        #course_id = request.query_params.get('course_id')
        sessions = services.get_user_chat_sessions(request.user.id)
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ChatMessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        before = request.query_params.get('before')
        before = int(before) if before else None
        
        if not session_id:
            return Response({"error": "session_id is required"}, status=400)

        chats = services.get_user_chat(
            user_id=request.user.id,
            session_id=int(session_id)
        )

        serializer = ChatMessageSerializer(chats, many=True)
        return Response(serializer.data)
    
class ChatMessageSendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
    
        if serializer.is_valid():
            success, result_or_stream, session_id = services.process_chat_message(
                request.user, 
                serializer.validated_data
            )
            
            if not success:
                return JsonResponse({"success": False, "error": result_or_stream}, status=400)
            response = StreamingHttpResponse(result_or_stream(), content_type='text/event-stream')
            response['X-Chat-Session-Id'] = str(session_id) 
            return response
        
        return JsonResponse({
                "success": False, 
                "error": "Dữ liệu đầu vào không hợp lệ",
                "details": serializer.errors
            }, status=400)