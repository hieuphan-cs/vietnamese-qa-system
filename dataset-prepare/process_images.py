import os
import json
import time
import google.generativeai as genai
from PIL import Image

# ==========================================
# CẤU HÌNH API KEY (Thay bằng key của bạn)
# ==========================================
#GOOGLE_API_KEY = "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"
GOOGLE_API_KEY = "AIzaSyAHA1_AU35OikaY_amqnEDWIW3HdE8LPns"
genai.configure(api_key=GOOGLE_API_KEY)

# 1. KHAI BÁO SYSTEM PROMPT CỰC CHUẨN
SYSTEM_PROMPT = """Bạn là công cụ OCR chuyên nghiệp cho văn bản hành chính và quy chế đại học Việt Nam.
    Nhiệm vụ: trích xuất toàn bộ nội dung từ ảnh scan và trả về JSON hợp lệ.
    Quy tắc:
    - Chỉ trả về chuẩn JSON, không có markdown (không dùng ```json), không giải thích.
    - Giữ nguyên cấu trúc Điều/Khoản/Mục.
    - Sửa các lỗi OCR rõ ràng (vd: "Điêu" -> "Điều") nhưng tuyệt đối không bịa thêm nội dung.
    - Nếu không nhận dạng được một đoạn, dùng "[không rõ]".
"""

# Khởi tạo mô hình với System Instruction và ép kiểu trả về là JSON
model = genai.GenerativeModel(
    model_name='gemini-3.1-flash-lite-preview',
    system_instruction=SYSTEM_PROMPT,
    generation_config={"response_mime_type": "application/json"}
)

def process_folder_with_ai(folder_path, folder_name):
    """Đọc toàn bộ ảnh trong 1 folder và gửi 1 lần cho Gemini"""
    
    # Lấy và sắp xếp file ảnh
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_files.sort()
    
    if not image_files:
        return None
        
    n_pages = len(image_files)
    print(f"   📸 Đang nạp {n_pages} trang của '{folder_name}'...")
    
    # Mở toàn bộ ảnh thành dạng đối tượng PIL Image
    images = []
    for img_file in image_files:
        img_path = os.path.join(folder_path, img_file)
        try:
            images.append(Image.open(img_path))
        except Exception as e:
            print(f"   [!] Lỗi mở ảnh {img_file}: {e}")
            
    # 2. KHAI BÁO USER PROMPT THEO TEMPLATE
    USER_PROMPT = f"""Đây là {n_pages} trang của một văn bản quy chế đại học (folder: {folder_name}).
        Hãy đọc toàn bộ các trang theo thứ tự và trích xuất nội dung.

        Trả về JSON với format sau (không có field nào khác):
        {{
        "source": "{folder_name}",
        "title": "<tiêu đề chính của văn bản>",
        "category": "<loại: quyet_dinh | quy_che | thong_bao | huong_dan | khac>",
        "content": "<toàn bộ nội dung văn bản, các điều/khoản cách nhau bằng \\n\\n>",
        "metadata": {{
            "so_hieu": "<số hiệu, vd: 2457/QĐ-TĐT hoặc null>",
            "ngay_ban_hanh": "<ngày ban hành, vd: 30/12/2017 hoặc null>",
            "co_quan_ban_hanh": "<tên trường/đơn vị hoặc null>",
            "nguoi_ky": "<tên người ký hoặc null>",
            "so_trang": {n_pages}
        }}
    }}"""

    # Gộp Prompt và danh sách hình ảnh vào 1 mảng để gửi đi
    request_content = [USER_PROMPT] + images
    
    print(f" Đang gửi {n_pages} trang cho AI xử lý...")
    try:
        response = model.generate_content(request_content)
        # Parse JSON trả về
        result_json = json.loads(response.text)
        return result_json
    except Exception as e:
        print(f"   [!] Lỗi API hoặc lỗi parse JSON: {e}")
        # In ra raw text để xem Gemini trả về cái gì mà lỗi
        try:
             print(f"   Raw output: {response.text}")
        except:
             pass
        return None

def process_images_with_ai(image_dir, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    folders = [f for f in os.listdir(image_dir) if os.path.isdir(os.path.join(image_dir, f))]
    
    print(f"Bắt đầu xử lý {len(folders)} thư mục tài liệu...")
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for folder_name in folders:
            folder_path = os.path.join(image_dir, folder_name)
            print(f"\n📂 Đang xử lý: {folder_name}")
            
            result = process_folder_with_ai(folder_path, folder_name)
            
            if result:
                # Ghi thẳng object JSON mà AI trả về vào file jsonl
                outfile.write(json.dumps(result, ensure_ascii=False) + '\n')
                print("   ✅ Trích xuất thành công!")
            else:
                print("   ❌ Trích xuất thất bại!")
                
            # Nghỉ 5 giây giữa các folder để tránh lỗi Rate Limit
            time.sleep(5)

    print("\n" + "="*40)
    print(f"🎉 Hoàn tất quá trình OCR Pro! Dữ liệu được lưu tại: {output_file}")

if __name__ == "__main__":
    # 1. Lấy đường dẫn của thư mục chứa script hiện tại (tức là thư mục 'data-pipeline')
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Lùi lại 1 cấp để lấy đường dẫn thư mục gốc của dự án
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    
    # 3. Nối đường dẫn từ thư mục gốc vào thư mục data
    IMAGE_DIRECTORY = os.path.join(PROJECT_ROOT, "data", "image")
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_images_knowledge_base.jsonl")
    
    # Đảm bảo tên hàm gọi đúng với tên hàm bạn đã định nghĩa ở trên (main hoặc process_images_with_ai)
    process_images_with_ai(IMAGE_DIRECTORY, OUTPUT_FILE)