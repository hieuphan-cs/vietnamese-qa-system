import os
import logging
import fitz  # Thư viện PyMuPDF đọc PDF
import docx  # Thư viện python-docx đọc Word
from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from .models import Document

logger = logging.getLogger(__name__)
chroma_client = chromadb.HttpClient(host='chromadb', port=8000)

def extract_pages_from_file(file_path: str, file_extension: str) -> list:
    #tách chữ từ file vật lý -> trả về danh sách: [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}]
    pages_data = []
    try:
        if file_extension == '.pdf':
            doc = fitz.open(file_path)
            if len(doc) == 0:
                raise ValueError("File PDF trống hoặc bị lỗi cấu trúc.")
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # --- ĐÃ SỬA CÁCH 1: Cắt bỏ 10% Header và 10% Footer ---
                rect = page.rect
                clip_rect = fitz.Rect(
                    rect.x0, 
                    rect.y0 + (rect.height * 0.1),  # Bỏ 10% lề trên
                    rect.x1, 
                    rect.y1 - (rect.height * 0.1)   # Bỏ 10% lề dưới
                )
                
                # Trích xuất text dựa trên khung đã cắt
                text = page.get_text("text", clip=clip_rect).strip()
                # --------------------------------------------------------
                
                if text:
                    # PyMuPDF đếm từ 0, ta cộng 1 để ra đúng số trang thực tế
                    pages_data.append({"page": page_num + 1, "text": text})
                    
        elif file_extension in ['.docx']:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs]).strip()
            if text:
                # Word không chia trang cố định, gán page = -1 để bypass
                pages_data.append({"page": -1, "text": text})
                
        elif file_extension in ['.txt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            if text:
                # Text file cũng không có trang, gán page = -1
                pages_data.append({"page": -1, "text": text})
        else:
            raise ValueError(f"Định dạng {file_extension} không được hỗ trợ xử lý nội dung.")
        
        if not pages_data:
            raise ValueError("Không tìm thấy nội dung văn bản trong file.")     
    except Exception as e:
        print(f"Error reading file: {file_path}: {e}")
        return []
    
    return pages_data

def chunk_text(text: str) -> list:
    # Bước 2: Băm nhỏ văn bản (Chunking) - Đã có chunk_overlap=200 rất chuẩn
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,       # Mỗi đoạn khoảng 1000 ký tự
        chunk_overlap=200,     # Các đoạn gối đầu lên nhau 200 ký tự
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    return chunks

def _rollback_document_creation(doc):
    #Hàm phụ để dọn dẹp khi quá trình embedding thất bại
    try:
        # Xóa vector (nếu đã kịp insert một phần)
        collection = chroma_client.get_collection(settings.CHROMA_COLLECTION_NAME)
        collection.delete(where={"document_id": doc.id})
    except: pass

    # Xóa file vật lý
    if doc.file and os.path.exists(doc.file.path):
        os.remove(doc.file.path)

    # KHÔNG XÓA RECORD DB, CHỈ ĐỔI TRẠNG THÁI THÀNH LỖI
    doc.status = Document.StatusChoices.FAILED
    doc.save()
    
def process_and_embed_document(document_id: int):
    # Bước 3: Hàm tổng kết nối các bước và gọi API Vector DB
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return None, False, "Không tìm thấy tài liệu trong hệ thống."
    try:
        doc.status = Document.StatusChoices.PROCESSING
        doc.save()
        
        file_path = doc.file.path
        file_extension = doc.file_type

        # 1. Trích xuất chữ THEO TỪNG TRANG
        pages_data = extract_pages_from_file(file_path, file_extension)
        if not pages_data:
            # Nếu file hỏng/không đọc được, cập nhật status
            doc.status = Document.StatusChoices.FAILED 
            doc.save()
            return doc, False, "Lỗi trích xuất nội dung: Không tìm thấy chữ hoặc định dạng không hợp lệ."

        all_chunks = []
        metadatas = []
        global_chunk_index = 0

        # 2 & 3. Băm nhỏ văn bản TỪNG TRANG & Tạo Metadata kẹp số trang
        for page_info in pages_data:
            page_text = page_info["text"]
            page_num = page_info["page"]
            
            # Băm nhỏ nội dung của riêng trang này
            chunks = chunk_text(page_text)
            
            if not chunks:
                continue
                
            for chunk in chunks:
                all_chunks.append(chunk)
                metadatas.append({
                    "document_id": doc.id,
                    "course_id": doc.course.id,  # Lưu môn học vào VectorDB
                    "title": doc.title,
                    "page": page_num,            
                    "chunk_index": global_chunk_index
                })
                global_chunk_index += 1

        if not all_chunks:
            return doc, False, "Không thể phân mảnh nội dung tài liệu."

        # Dùng AI Local của HuggingFace để chạy trên máy
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        # 5. Lưu vào ChromaDB
        vectorstore = Chroma(
            client=chroma_client,
            embedding_function=embeddings_model,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        try:
            vectorstore.add_texts(
                texts=all_chunks,
                metadatas=metadatas
            )

            collection = chroma_client.get_collection(settings.CHROMA_COLLECTION_NAME)
            print("Total after insert:", collection.count())
            
            #Thành công => Đổi trạng thái file thành READY
            doc.status = Document.StatusChoices.READY
            doc.save()

            return doc, True, f"Xử lý thành công! Đã tạo {len(all_chunks)} đoạn dữ liệu."
        except Exception as e:
            print("Embedding error:", str(e))

            _rollback_document_creation(doc)
            return None, False, f"Lỗi khi lưu vào cơ sở dữ liệu vector: {str(e)}"

    except Exception as e:
        logger.error(f"General processing error: {str(e)}")
        return doc, False, f"Lỗi hệ thống không xác định: {str(e)}"