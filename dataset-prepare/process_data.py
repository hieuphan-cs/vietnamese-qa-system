import os
import json

def clean_crawled_json(json_data):
    """Hàm làm sạch dữ liệu (như đã viết ở trên)"""
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    if data.get("status") != "success":
        return None

    url = data.get("url", "")
    title = data.get("title", "")
    label = data.get("label", "")
    category = data.get("topic", "")
    cleaned_text_blocks = []
    
    if title:
        cleaned_text_blocks.append(f"{title.upper()}\n")

    for p in data.get("paragraphs", []):
        tag = p.get("tag", "")
        text = p.get("text", "").strip()
        
        if not text:
            continue

        if tag in ["h1", "h2", "h3"]:
            if text.lower() != title.lower():
                cleaned_text_blocks.append(f"\n[{text}]") 
        elif tag == "li":
            cleaned_text_blocks.append(f"- {text}")
        elif tag == "p":
            cleaned_text_blocks.append(text)
        else:
            cleaned_text_blocks.append(text)

    full_text = "\n".join(cleaned_text_blocks).strip()

    return {
        "source": label,
        "source_url": url,
        "title": title,
        "category": category,
        "content": full_text,
        "metadata": {}
    }

def process_all_files(input_dir, output_file):
    """Duyệt qua tất cả file JSON và lưu thành file JSONL"""
    # Tự động tạo thư mục đầu ra nếu chưa có
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    valid_articles_count = 0
    
    # Mở file đầu ra ở chế độ ghi
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # Duyệt qua các file trong thư mục input_dir
        for filename in os.listdir(input_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(input_dir, filename)
                print(f"Đang xử lý file: {filename}...")
                
                with open(filepath, 'r', encoding='utf-8') as in_f:
                    try:
                        data = json.load(in_f)
                        
                        # Xử lý trường hợp file json chứa 1 list nhiều bài viết
                        if isinstance(data, list):
                            for item in data:
                                cleaned = clean_crawled_json(item)
                                if cleaned:
                                    out_f.write(json.dumps(cleaned, ensure_ascii=False) + '\n')
                                    valid_articles_count += 1
                        # Xử lý trường hợp file json chỉ chứa 1 bài viết
                        else:
                            cleaned = clean_crawled_json(data)
                            if cleaned:
                                out_f.write(json.dumps(cleaned, ensure_ascii=False) + '\n')
                                valid_articles_count += 1
                                
                    except json.JSONDecodeError:
                        print(f" Lỗi: File {filename} không đúng định dạng JSON.")

    print("-" * 30)
    print(f"Hoàn tất! Đã làm sạch và lưu {valid_articles_count} bài viết.")
    print(f"File kết quả: {output_file}")

# --- THỰC THI SCRIPT ---
if __name__ == "__main__":
    
    # 1. Lấy đường dẫn của thư mục chứa script hiện tại (thư mục 'data-pipeline')
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Lùi lại 1 cấp để lấy đường dẫn thư mục gốc của dự án
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) 
    
    # 3. Nối đường dẫn từ thư mục gốc vào thư mục data
    RAW_DIRECTORY = os.path.join(PROJECT_ROOT, "data", "raw", "public")
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_knowledge_base.jsonl")
    
    process_all_files(RAW_DIRECTORY, OUTPUT_FILE)