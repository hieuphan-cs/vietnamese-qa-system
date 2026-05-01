import os
import json
import time
import random # Thư viện cần thiết để xáo trộn tập test
import google.generativeai as genai

# ==========================================
# CẤU HÌNH API KEY
# ==========================================
#GOOGLE_API_KEY = "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"
GOOGLE_API_KEY = "AIzaSyCZeblpbFanMxbcXSE_oUwxLxQCTvvQtNg"
genai.configure(api_key=GOOGLE_API_KEY)

# Sử dụng gemini-1.5-flash để đảm bảo ổn định
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
pair_qa = 2
def clean_json_response(text):
    """Hàm dọn dẹp các ký tự thừa (như markdown ```json) mà LLM hay thêm vào."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
        
    return text.strip()

def generate_and_split_qa(input_filepath, train_output, test_output, test_size=50):
    os.makedirs(os.path.dirname(train_output), exist_ok=True)

    # File tạm lưu QA đã gen, dùng để resume
    temp_output = train_output.replace('.jsonl', '_temp.jsonl')

    # Đọc lại số chunk đã xử lý từ file tạm (nếu có)
    processed_chunks = 0
    all_qa_pairs = []

    if os.path.exists(temp_output):
        with open(temp_output, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_qa_pairs.append(json.loads(line))
        # Mỗi chunk gen 3 cặp QA → số chunk đã xử lý = số QA / 3
        processed_chunks = len(all_qa_pairs) // pair_qa
        print(f"⏩ Resume: đã có {len(all_qa_pairs)} QA ({processed_chunks} chunk), tiếp tục từ chunk {processed_chunks + 1}...")

    chunk_count = 0
    skipped_short = 0
    
    print(f"Bắt đầu đọc dữ liệu từ: {input_filepath}")

    with open(input_filepath, 'r', encoding='utf-8') as infile, \
         open(temp_output, 'a', encoding='utf-8') as temp_f:  # ✅ 'a' để không ghi đè

        for line in infile:
            if not line.strip():
                continue

            doc = json.loads(line)
            content = doc.get("content", "")

            if len(content.split()) < 20:
                skipped_short += 1
                print(f"   ⏭️  Bỏ qua chunk quá ngắn ({len(content.split())} words)")
                continue

            chunk_count += 1

            # ✅ Bỏ qua các chunk đã xử lý
            if chunk_count <= processed_chunks:
                print(f"⏩ Bỏ qua chunk {chunk_count} (đã có)")
                continue

            print(f"Đang xử lý chunk thứ {chunk_count}... (Đã tạo: {len(all_qa_pairs)} QA)")

            prompt = f"""Bạn là một chuyên gia tạo dữ liệu huấn luyện AI cho hệ thống giáo dục.
            Dựa vào đoạn quy chế đại học dưới đây, hãy tạo ra {pair_qa} cặp câu hỏi và câu trả lời.

            YÊU CẦU NGHIÊM NGẶT:
                1. Câu hỏi (instruction): Đóng vai trò là sinh viên đang thắc mắc, văn phong tự nhiên.
                2. Câu trả lời (output): Đóng vai trò là trợ lý nhà trường, trả lời chính xác, đầy đủ dựa trên đoạn quy chế, KHÔNG BỊA ĐẶT thông tin ngoài.
                3. KẾT QUẢ TRẢ VỀ CHỈ ĐƯỢC PHÉP LÀ MỘT MẢNG JSON HỢP LỆ, không có bất kỳ văn bản giải thích nào khác.

            ĐỊNH DẠNG JSON MẪU:
            [
                {{"instruction": "Sinh viên muốn xem lại điểm thi thì làm thế nào ạ?", "output": "Để xem lại điểm thi, sinh viên cần nộp đơn phúc khảo..."}}
            ]

            ĐOẠN QUY CHẾ:
            {content}
            """

            try:
                response = model.generate_content(prompt)
                raw_text = clean_json_response(response.text)
                qa_pairs = json.loads(raw_text)

                for qa in qa_pairs:
                    qa["source_title"] = doc.get("title", "Unknown")
                    qa["metadata"] = doc.get("metadata", {})
                    all_qa_pairs.append(qa)
                    # ✅ Ghi ngay vào file tạm, không bị mất nếu crash
                    temp_f.write(json.dumps(qa, ensure_ascii=False) + '\n')

                temp_f.flush()  # ✅ Đảm bảo ghi xuống disk

            except Exception as e:
                print(f"  [!] Lỗi ở chunk {chunk_count}: {str(e)[:100]}... Bỏ qua.")

            time.sleep(4)

    # Xáo trộn và chia train/test
    total_qa = len(all_qa_pairs)
    print(f"\n🎉 Đã gen xong tổng cộng {total_qa} câu QA.")

    if total_qa < test_size:
        print(f"⚠️ Số QA ({total_qa}) ít hơn test_size ({test_size}). Không thể chia file.")
        return

    random.shuffle(all_qa_pairs)
    test_set = all_qa_pairs[:test_size]
    train_set = all_qa_pairs[test_size:]

    with open(test_output, 'w', encoding='utf-8') as f:
        for item in test_set:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open(train_output, 'w', encoding='utf-8') as f:
        for item in train_set:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    # ✅ Xóa file tạm sau khi chia xong
    if os.path.exists(temp_output):
        os.remove(temp_output)
        print(f"🗑️  Đã xóa file tạm: {temp_output}")

    print(f"\n📊 Thống kê:")
    print(f"   Tổng dòng trong file : {chunk_count + skipped_short}")
    print(f"   Chunk hợp lệ đã gen  : {chunk_count}")
    print(f"   Chunk quá ngắn skip  : {skipped_short}")
    print("-" * 40)
    print(f"✅ Tập TEST:  {len(test_set)} câu → {test_output}")
    print(f"✅ Tập TRAIN: {len(train_set)} câu → {train_output}")

if __name__ == "__main__":
    # Setup đường dẫn tương đối chuẩn xác
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    
    # Cấu hình các file đầu vào và đầu ra
    INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "chunked_knowledge_base.jsonl")
    
    # Đầu ra: Định tuyến sang thư mục 'dataset' mới
    # Thư mục 'dataset' này nằm bên trong thư mục 'data'
    DATASET_DIR = os.path.join(PROJECT_ROOT, "data", "dataset")
    
    TRAIN_FILE = os.path.join(DATASET_DIR, "train_qa.jsonl")
    TEST_FILE = os.path.join(DATASET_DIR, "test_qa.jsonl")
    
    # Chạy hàm với kích thước tập test là 50
    generate_and_split_qa(INPUT_FILE, TRAIN_FILE, TEST_FILE, test_size=50)