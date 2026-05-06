from .models import ChatSession, ChatMessage
from rest_framework import serializers

class ChatMessageSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%H:%M %d-%m-%Y")
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender_role', 'content', 'created_at']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'created_at', 'messages']

class ChatInputSerializer(serializers.Serializer):
    #course_id = serializers.IntegerField()
    message = serializers.CharField(max_length=2000)
    session_id = serializers.IntegerField(required=False, allow_null=True)
    model_name = serializers.CharField(required=False, allow_null=True, default="gemini-2.5-flash") # THÊM DÒNG NÀY