import os
import json
import time
import google.generativeai as genai

# ==========================================
# CẤU HÌNH API KEY (Thay bằng key của bạn)
# ==========================================
GOOGLE_API_KEY = "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"

genai.configure(api_key=GOOGLE_API_KEY)

# Sử dụng mô hình Gemini 1.5 Flash (Nhanh, thông minh và phù hợp cho tác vụ này)
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

def generate_qa_dataset(input_filepath, output_filepath, target_qa=300):
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    
    generated_count = 0
    chunk_count = 0
    
    print(f"Bắt đầu đọc dữ liệu từ: {input_filepath}")
    
    # Mở file ghi (mode 'a' để ghi tiếp nếu script bị dừng giữa chừng)
    with open(output_filepath, 'a', encoding='utf-8') as outfile:
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            for line in infile:
                if generated_count >= target_qa:
                    print(f"\n🎉 Đã đạt mục tiêu {target_qa} câu QA. Tự động dừng!")
                    break
                    
                if not line.strip():
                    continue
                
                doc = json.loads(line)
                content = doc.get("content", "")
                
                # Bỏ qua các chunk quá ngắn (ít thông tin để hỏi)
                if len(content.split()) < 20:
                    continue
                
                chunk_count += 1
                print(f"Đang xử lý chunk thứ {chunk_count}... (Đã tạo: {generated_count} QA)")
                
                # Xây dựng Prompt "ép" mô hình trả về chuẩn JSON
                prompt = f"""Bạn là một chuyên gia tạo dữ liệu huấn luyện AI cho hệ thống giáo dục.
                    Dựa vào đoạn quy chế đại học dưới đây, hãy tạo ra 6 cặp câu hỏi và câu trả lời.

                    YÊU CẦU NGHIÊM NGẶT:
                    1. Câu hỏi (instruction): Đóng vai trò là sinh viên đang thắc mắc, văn phong tự nhiên.
                    2. Câu trả lời (output): Đóng vai trò là trợ lý nhà trường, trả lời chính xác, đầy đủ dựa trên đoạn quy chế, KHÔNG BỊA ĐẶT thông tin ngoài.
                    3. KẾT QUẢ TRẢ VỀ CHỈ ĐƯỢC PHÉP LÀ MỘT MẢNG JSON HỢP LỆ, không có bất kỳ văn bản giải thích nào khác.

                    ĐỊNH DẠNG JSON MẪU:
                    [
                        {{"instruction": "Sinh viên muốn xem lại điểm thi thì làm thế nào ạ?", "output": "Để xem lại điểm thi, sinh viên cần nộp đơn phúc khảo..."}},
                        {{"instruction": "Quy định về thời gian đóng học phí là khi nào?", "output": "Theo quy chế, thời gian đóng học phí..."}}
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
                    
                    # Ghi từng cặp QA vào file jsonl
                    for qa in qa_pairs:
                        # Thêm metadata để biết câu QA này được sinh từ bài nào
                        qa["source_title"] = doc.get("title", "Unknown") 
                        outfile.write(json.dumps(qa, ensure_ascii=False) + '\n')
                        generated_count += 1
                        
                except Exception as e:
                    print(f"  [!] Lỗi ở chunk {chunk_count}: {str(e)[:100]}... Bỏ qua và đi tiếp.")
                
                # NGHỈ 3 GIÂY: Bước lách luật giới hạn (Rate Limit) của bản miễn phí
                time.sleep(3)

    print("-" * 40)
    print(f"Hoàn tất! Đã lưu {generated_count} cặp QA vào file: {output_filepath}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Đầu vào: File chunked
    INPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "chunked_knowledge_base.jsonl")
    
    # Đầu ra: File chứa 300+ cặp QA dùng để Fine-tune
    OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "train_qa.jsonl")
    
    # Chạy hàm với mục tiêu sinh 300 câu
    generate_qa_dataset(INPUT_FILE, OUTPUT_FILE, target_qa=324)