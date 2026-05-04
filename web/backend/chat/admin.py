from django.contrib import admin
from .models import ChatSession, ChatMessage

class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'title', 'created_at')

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender_role', 'created_at')

admin.site.register(ChatSession, ChatSessionAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)