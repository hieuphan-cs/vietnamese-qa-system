from django.urls import path, include
from django.urls import path
from .views import DocumentListCreateAPIView, DocumentDetailAPIView

urlpatterns = [
    path('', DocumentListCreateAPIView.as_view(), name='document-list'),
    
    path('<int:pk>/', DocumentDetailAPIView.as_view(), name='document-detail'),
]