import os
import json
import time
import random # Thư viện cần thiết để xáo trộn tập test
import google.generativeai as genai

# ==========================================
# CẤU HÌNH API KEY
# ==========================================
#GOOGLE_API_KEY = "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"
GOOGLE_API_KEY = "AIzaSyAHA1_AU35OikaY_amqnEDWIW3HdE8LPns"
genai.configure(api_key=GOOGLE_API_KEY)

# Sử dụng gemini-1.5-flash để đảm bảo ổn định
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

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
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(train_output), exist_ok=True)
    
    all_qa_pairs = [] # Mảng chứa toàn bộ QA sinh ra
    chunk_count = 0
    
    print(f"Bắt đầu đọc dữ liệu từ: {input_filepath}")
    
    with open(input_filepath, 'r', encoding='utf-8') as infile:
        for line in infile:
            if not line.strip(): 
                continue
            
            doc = json.loads(line)
            content = doc.get("content", "")
            
            # Bỏ qua các chunk quá ngắn
            if len(content.split()) < 20: 
                continue
            
            chunk_count += 1
            print(f"Đang xử lý chunk thứ {chunk_count}... (Đã tạo: {len(all_qa_pairs)} QA)")
            
            # Yêu cầu gen 3 câu/chunk để dữ liệu đa dạng và tránh quá tải token
            prompt = f"""Bạn là một chuyên gia tạo dữ liệu huấn luyện AI cho hệ thống giáo dục.
            Dựa vào đoạn quy chế đại học dưới đây, hãy tạo ra 3 cặp câu hỏi và câu trả lời.

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
                # Gọi API Gemini
                response = model.generate_content(prompt)
                
                # Trích xuất và parse JSON
                raw_text = clean_json_response(response.text)
                qa_pairs = json.loads(raw_text)
                
                # Thêm metadata và đẩy vào mảng tổng
                for qa in qa_pairs:
                    qa["source_title"] = doc.get("title", "Unknown") 
                    qa["metadata"] = doc.get("metadata", {}) # Lấy metadata cho dữ liệu ảnh
                    all_qa_pairs.append(qa)
                    
            except Exception as e:
                print(f"  [!] Lỗi ở chunk {chunk_count}: {str(e)[:100]}... Bỏ qua và đi tiếp.")
            
            # NGHỈ 4 GIÂY để tránh Rate Limit của bản miễn phí
            time.sleep(4)

    # ==========================================
    # TIẾN HÀNH XÁO TRỘN VÀ CHIA FILE
    # ==========================================
    total_qa = len(all_qa_pairs)
    print(f"\n🎉 Đã gen xong tổng cộng {total_qa} câu QA.")
    
    if total_qa < test_size:
        print(f"⚠️ Cảnh báo: Số QA sinh ra ({total_qa}) ít hơn số test_size ({test_size}). Không thể chia file.")
        return

    print("Đang xáo trộn ngẫu nhiên và chia tập Train/Test...")
    
    # 1. Xáo trộn ngẫu nhiên toàn bộ danh sách QA
    random.shuffle(all_qa_pairs)
    
    # 2. Cắt lấy 50 câu đầu tiên cho tập Test
    test_set = all_qa_pairs[:test_size]
    
    # 3. Lấy phần còn lại cho tập Train
    train_set = all_qa_pairs[test_size:]
    
    # Ghi file Test
    with open(test_output, 'w', encoding='utf-8') as f:
        for item in test_set:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    # Ghi file Train
    with open(train_output, 'w', encoding='utf-8') as f:
        for item in train_set:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print("-" * 40)
    print(f"Hoàn tất! Dữ liệu đã được chia thành công:")
    print(f" - Tập TEST:  {len(test_set)} câu -> {test_output}")
    print(f" - Tập TRAIN: {len(train_set)} câu -> {train_output}")

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