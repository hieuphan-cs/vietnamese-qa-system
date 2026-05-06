from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Document
from .serializers import DocumentSerializer
from .services import create_document_service, delete_document_service
from config.permissions import IsAdminOrTeacher

class DocumentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    parser_classes = (MultiPartParser, FormParser)
    
    def get(self, request):
        user = request.user
        if user.is_admin:
            documents = Document.objects.all()
        else:
            documents = Document.objects.filter(uploaded_by=user)
        
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_admin and not request.user.is_teacher:
            return Response({
                "success": False,
                "message": "Bạn không có quyền đăng tài liệu. Chỉ Admin hoặc Giáo viên mới có quyền này!",
                "data": None,
                "errors": None
            }, status=status.HTTP_403_FORBIDDEN)
        
        course_id = request.data.get("course_id")
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response({
                "success": False,
                "message": "Vui lòng chọn file",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        result = create_document_service(
            user=request.user,
            course_id=course_id,
            file_obj=file_obj
        )

        if result["success"]:
            doc_instance = result["data"]
            result["data"] = DocumentSerializer(doc_instance).data
            result["is_new"] = True
            return Response(result, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "message": result["message"],
            "data": None,
            "errors": result.get("errors")
        }, status=status.HTTP_400_BAD_REQUEST)


class DocumentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    def patch(self, request, pk):
        """Cập nhật thông tin Document (PATCH)"""
        instance = get_object_or_404(Document, pk=pk)

        # Kiểm tra quyền: Chỉ Admin hoặc người upload mới được sửa
        if not request.user.is_admin and instance.uploaded_by != request.user:
            return Response({
                "status": False,
                "message": "You do not have permission to edit this document.",
                "data": None,
                "error": None
                }, status=status.HTTP_403_FORBIDDEN
            )

        # partial=True cho phép cập nhật không bắt buộc truyền đủ các fields
        serializer = DocumentSerializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Cập nhật tài liệu thành công",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Lấy object hoặc trả về 404
        instance = get_object_or_404(Document, pk=pk)
        
        # Kiểm tra quyền
        if not request.user.is_admin and instance.uploaded_by != request.user:
            return Response({
                "status": False,
                "message": "Không thể xóa tài liệu do người khác đăng",
                "data": None,
                "error": None
            }, status=status.HTTP_403_FORBIDDEN)

        result = delete_document_service(instance)
        
        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
