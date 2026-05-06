from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import json
import os

def embed_and_store(chunks_filepath):
    # ✅ Trỏ thẳng vào chromadb của project web
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    CHROMA_PATH = os.path.join(PROJECT_ROOT, "web", "backend", "chroma_data")

    print("Đang tải embedding model...")
    embeddings_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    print(f"Kết nối ChromaDB tại: {CHROMA_PATH}")
    vectordb = Chroma(
        collection_name="my_reference_documents",
        embedding_function=embeddings_model,
        persist_directory=CHROMA_PATH
    )

    # Đọc chunks và thêm vào vectordb
    texts = []
    metadatas = []
    ids = []

    print(f"Đọc chunks từ: {chunks_filepath}")
    with open(chunks_filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            doc = json.loads(line)

            texts.append(doc.get("content", ""))
            metadatas.append({
                "source": doc.get("source", ""),
                "source_url": doc.get("source_url") or "",  # ChromaDB không nhận None
                "title": doc.get("title", ""),
                "category": doc.get("category", ""),
                "chunk_id": doc.get("chunk_id", ""),
            })
            ids.append(doc.get("chunk_id", f"chunk_{len(ids)}"))

    print(f"Đang embed và lưu {len(texts)} chunks vào ChromaDB...")
    
    # Thêm theo batch để tránh quá tải memory
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_meta = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        vectordb.add_texts(
            texts=batch_texts,
            metadatas=batch_meta,
            ids=batch_ids
        )
        print(f"   ✅ Đã lưu batch {i//batch_size + 1}/{(len(texts)+batch_size-1)//batch_size}")

    print(f"\n🎉 Hoàn tất! Đã lưu {len(texts)} chunks vào ChromaDB")
    print(f"📁 Đường dẫn: {CHROMA_PATH}")
    print(f"📊 Tổng documents trong DB: {vectordb._collection.count()}")


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    CHUNKS_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "chunked_knowledge_base.jsonl")
    
    embed_and_store(CHUNKS_FILE)