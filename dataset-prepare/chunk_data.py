import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

def create_chunks(input_filepath, output_filepath, chunk_size=500, chunk_overlap=50):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    total_chunks = 0

    print(f"Đọc dữ liệu từ: {input_filepath}")
    with open(input_filepath, 'r', encoding='utf-8') as infile, \
         open(output_filepath, 'a', encoding='utf-8') as outfile:

        for line in infile:
            if not line.strip():
                continue

            doc = json.loads(line)
            content = doc.get("content", "")

            if not content:
                continue

            chunks = text_splitter.split_text(content)

            for i, chunk_text in enumerate(chunks):
                chunk_doc = {
                    "source": doc.get("source", ""),
                    "source_url": doc.get("source_url", ""),
                    "title": doc.get("title", ""),
                    "category": doc.get("category", ""),
                    "chunk_id": f"{doc.get('source', 'doc')}_chunk_{i}",
                    "content": chunk_text,
                    "metadata": doc.get("metadata", {})
                }
                outfile.write(json.dumps(chunk_doc, ensure_ascii=False) + '\n')
                total_chunks += 1

    print("-" * 30)
    print(f"Hoàn tất! Đã chia nhỏ thành {total_chunks} chunks.")
    print(f"Dữ liệu sẵn sàng cho VectorDB được lưu tại: {output_filepath}")


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    
    # File đầu vào (kết quả từ bước trước)
    #INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_knowledge_base.jsonl")
    INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_images_knowledge_base.jsonl")
    # File đầu ra (đã chia chunk)
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "chunked_knowledge_base.jsonl")

    create_chunks(INPUT_FILE, OUTPUT_FILE, chunk_size=1000, chunk_overlap=200)