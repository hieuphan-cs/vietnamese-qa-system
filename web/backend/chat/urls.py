from django.urls import path
from . import views

urlpatterns = [
    # GET /api/chat/sessions/ -> Lấy danh sách phiên chat
    path('sessions/', views.ChatSessionListView.as_view(), name='chat-session-list'),
    
    # POST /api/chat/send/ -> Gửi tin nhắn
    path('send/', views.ChatMessageSendView.as_view(), name='chat-send-message'),
    
    # Get /api/chat/ -> Xem tin nhắn
    path('sessions/<int:session_id>/', views.ChatMessageListView.as_view(), name='chat-view-message'),
]