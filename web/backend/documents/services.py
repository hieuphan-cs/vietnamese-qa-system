import os
import hashlib
import threading # Dùng để chạy ngầm tiến trình AI
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.conf import settings
import logging
import chromadb

from .models import Document
from courses.models import Course
from .rag_services import process_and_embed_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
chroma_client = chromadb.HttpClient(host='chromadb', port=8000)

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt']

def create_document_service(user, course_id, file_obj):
    # Lấy thông tin phụ của file
    file_size = file_obj.size  # Đơn vị: bytes
    file_extension = os.path.splitext(file_obj.name)[1].lower()
    title = file_obj.name
    
    # Kiểm tra dung lượng
    if file_size > MAX_FILE_SIZE:
       return {
                "success": False,
                "message": f"File quá lớn! Dung lượng tối đa cho phép là {MAX_FILE_SIZE / (1024*1024):.2f} MB.",
                "data": None
            }
    
    # Check course tồn tại
    course = get_object_or_404(Course, id=course_id)
    
    # Check extension
    if file_extension not in ALLOWED_EXTENSIONS:
        return {
            "success": False,
            "message": f"Định dạng {file_extension} không được hỗ trợ. Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}",
            "data": None
        }
        
    hasher = hashlib.md5()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    file_hash = hasher.hexdigest()
    file_obj.seek(0) # Reset con trỏ file
    
    existing_doc = Document.objects.filter(checksum=file_hash, course=course).first()
    if existing_doc:
        return {
                "success": False,
                "message": f"Tài liệu '{existing_doc.title}' đã tồn tại trong khóa học này.",
                "data": existing_doc
            }

    doc = Document.objects.create(
        course=course,
        title=title,
        file=file_obj,
        file_size=file_obj.size,
        file_type=file_extension,
        uploaded_by=user,
        checksum=file_hash,
        status=Document.StatusChoices.PROCESSING 
    )

    thread = threading.Thread(target=process_and_embed_document, args=(doc.id,))
    thread.start()
        
    return {
        "success": True,
        "message": f"Tài liệu '{doc.title}' đang được AI xử lý ngầm!",
        "data": doc
    }


def delete_document_service(document_instance):
    document_title = document_instance.title
    try:
        # 1. Xoá vector trong Chroma
        try:
            collection = chroma_client.get_collection(settings.CHROMA_COLLECTION_NAME)
            collection.delete(where={"document_id": document_instance.id})
            print(f"Deleted vectors for document {document_instance.id}")
        except Exception as e:
            print(f"Vector delete error: {e}")

        # 2. Xoá file vật lý
        if document_instance.file:
            try:
                if os.path.isfile(document_instance.file.path):
                    os.remove(document_instance.file.path)
            except Exception as e:
                logger.error(f"Cannot delete physical file: {e}")

        # 3. Xoá DB
        document_instance.delete()
        return {
            "success": True,
            "message": f"Đã xóa tài liệu {document_title} thành công.",
            "data": None
        }
    except Exception as e:
        logger.error(f"Delete document failed: {e}")
        return {
            "success": False,
            "message": f"Lỗi hệ thống khi xóa tài liệu: {str(e)}",
            "data": None
        }