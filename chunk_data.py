import os
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker

def create_semantic_chunks(input_filepath, output_filepath):
    # 1. Khởi tạo model nhúng (MiniLM siêu nhẹ và nhanh)
    print("Đang tải model HuggingFace...")
    embeddings_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    # 2. Cấu hình bộ cắt văn bản theo ngữ nghĩa
    print("Đang cấu hình Semantic Chunker...")
    text_splitter = SemanticChunker(
        embeddings_model,
        breakpoint_threshold_type="percentile" # Cắt dựa trên sự thay đổi ngữ nghĩa
    )

    # Đảm bảo thư mục đầu ra tồn tại
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    
    total_chunks = 0
    
    # 3. Đọc dữ liệu đã làm sạch và tiến hành cắt
    print(f"Đọc dữ liệu từ: {input_filepath}")
    with open(input_filepath, 'r', encoding='utf-8') as infile, \
         open(output_filepath, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            if not line.strip():
                continue
            
            # Đọc từng bài viết dạng JSON
            doc = json.loads(line)
            content = doc.get("content", "")
            
            if not content:
                continue
            
            # Cắt nội dung thành các chunk theo ngữ nghĩa
            chunks = text_splitter.split_text(content)
            
            # Lưu từng chunk kèm metadata gốc
            for i, chunk_text in enumerate(chunks):
                chunk_doc = {
                    "source_url": doc.get("source_url", ""),
                    "title": doc.get("title", ""),
                    "category": doc.get("category", ""),
                    "chunk_id": f"{doc.get('title', 'doc')}_chunk_{i}",
                    "content": chunk_text
                }
                
                # Ghi chunk mới vào file jsonl
                outfile.write(json.dumps(chunk_doc, ensure_ascii=False) + '\n')
                total_chunks += 1

    print("-" * 30)
    print(f"Hoàn tất! Đã chia nhỏ thành {total_chunks} chunks.")
    print(f"Dữ liệu sẵn sàng cho VectorDB được lưu tại: {output_filepath}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # File đầu vào (kết quả từ bước trước)
    INPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "cleaned_knowledge_base.jsonl")
    
    # File đầu ra (đã chia chunk)
    OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "chunked_knowledge_base.jsonl")
    
    create_semantic_chunks(INPUT_FILE, OUTPUT_FILE)