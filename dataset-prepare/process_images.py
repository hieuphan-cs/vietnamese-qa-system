import os
import json
import time
import google.generativeai as genai
from PIL import Image

# ==========================================
# CẤU HÌNH API KEY (Thay bằng key của bạn)
# ==========================================

GOOGLE_API_KEY = "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"

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
    generation_config={
        "response_mime_type": "application/json",
        "max_output_tokens": 8192
    }
)

#Hàm lấy text an toàn, tránh crash khi finish_reason != STOP
def safe_get_text(response):
    if not response.candidates:
        print("   [!] Không có candidates trong response")
        return None

    candidate = response.candidates[0]
    finish_reason = candidate.finish_reason

    # finish_reason: 1=STOP, 2=MAX_TOKENS, 3=SAFETY, 4=COPYRIGHT, 5=OTHER
    if finish_reason == 4:
        print("   [!] Gemini từ chối vì copyright filter (finish_reason=4)")
        return None
    if finish_reason == 3:
        print("   [!] Gemini từ chối vì safety filter (finish_reason=3)")
        return None
    if finish_reason not in (0, 1):
        print(f"   [!] finish_reason không hợp lệ: {finish_reason}")
        return None

    if candidate.content and candidate.content.parts:
        return candidate.content.parts[0].text

    return None

#Gọi API với retry tự động
def generate_with_retry(request_content, max_retries=3, delay=2):
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(
                request_content,
                request_options={"timeout": 120}
            )
            text = safe_get_text(response)

            if text is None:
                print(f"   [!] Attempt {attempt}/{max_retries} thất bại, thử lại sau {delay}s...")
                time.sleep(delay)
                continue

            return text

        except Exception as e:
            print(f"   [!] Exception attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                time.sleep(delay)

    return None  # Hết retry vẫn fail

def process_folder_with_ai(folder_path, folder_name, batch_size=10):
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_files.sort()

    if not image_files:
        return None

    n_pages = len(image_files)
    total_batches = (n_pages + batch_size - 1) // batch_size
    print(f"   📸 {n_pages} trang → {total_batches} batch ({batch_size} trang/batch)")

    final_result = None

    for batch_idx, batch_start in enumerate(range(0, n_pages, batch_size)):
        batch_files = image_files[batch_start: batch_start + batch_size]
        batch_num = batch_idx + 1
        page_range = f"{batch_start + 1}-{batch_start + len(batch_files)}"
        print(f"   📦 Batch {batch_num}/{total_batches} (trang {page_range})...")

        images = []
        for img_file in batch_files:
            img_path = os.path.join(folder_path, img_file)
            try:
                images.append(Image.open(img_path))
            except Exception as e:
                print(f"   [!] Lỗi mở ảnh {img_file}: {e}")

        if batch_num == 1:
            prompt = f"""Đây là trang {page_range}/{n_pages} của một văn bản quy chế đại học (folder: {folder_name}).
Hãy đọc các trang theo thứ tự và trích xuất nội dung.

Trả về JSON với format sau (không có field nào khác):
{{
    "source": "{folder_name}",
    "source_url": null,
    "title": "<tiêu đề chính của văn bản>",
    "category": "<loại: quyet_dinh | quy_che | thong_bao | huong_dan | khac>",
    "content": "<nội dung các trang này, kết thúc tự nhiên, KHÔNG dùng dấu ... hay [tiếp theo]>",
    "metadata": {{
        "so_hieu": "<số hiệu, vd: 2457/QĐ-TĐT hoặc null>",
        "ngay_ban_hanh": "<ngày ban hành, vd: 30/12/2017 hoặc null>",
        "co_quan_ban_hanh": "<tên trường/đơn vị hoặc null>",
        "nguoi_ky": "<tên người ký hoặc null>",
        "so_trang": {n_pages}
    }}
}}"""
        else:
            prompt = f"""Đây là phần tiếp theo (trang {page_range}/{n_pages}) của văn bản '{folder_name}'.
Trích xuất nội dung tiếp nối, trả về JSON đơn giản (không có field nào khác):
{{"content": "<nội dung tiếp nối trực tiếp, KHÔNG có tiêu đề mới, KHÔNG lặp lại nội dung trước>"}}"""

        raw_text = generate_with_retry([prompt] + images)

        if raw_text is None:
            print(f"   [!] Batch {batch_num} thất bại sau tất cả retries, bỏ qua...")
            continue

        try:
            # ✅ Fix 1: Lấy JSON object đầu tiên nếu Gemini trả về nhiều object
            raw_text_stripped = raw_text.strip()
            decoder = json.JSONDecoder()
            batch_json, _ = decoder.raw_decode(raw_text_stripped)

            if batch_num == 1:
                final_result = batch_json
                print(f"   ✅ Batch {batch_num}: khởi tạo structure + {len(batch_json.get('content', ''))} ký tự")
            else:
                # ✅ Fix 2: Chỉ gộp nếu final_result đã tồn tại
                if final_result is None:
                    print(f"   [!] Batch {batch_num}: bỏ qua vì batch 1 chưa có kết quả")
                    continue
                extra_content = batch_json.get("content", "")
                final_result["content"] += "\n" + extra_content
                print(f"   ✅ Batch {batch_num}: gộp thêm {len(extra_content)} ký tự")

        except json.JSONDecodeError as e:
            print(f"   [!] Lỗi parse JSON batch {batch_num}: {e}")
            print(f"   Raw output: {raw_text[:300]}...")
            continue

        time.sleep(2)

    if final_result:
        print(f"   📝 Tổng content sau khi gộp: {len(final_result.get('content', ''))} ký tự")

    return final_result

def process_images_with_ai(image_dir, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    folders = sorted([f for f in os.listdir(image_dir) 
                      if os.path.isdir(os.path.join(image_dir, f))])

    # ✅ File log các folder thất bại
    failed_log = output_file.replace('.jsonl', '_failed.txt')
    
    # ✅ Đọc các folder đã xử lý thành công để resume
    processed = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    processed.add(obj.get('source', ''))
                except:
                    pass
        print(f"⏩ Resume: đã có {len(processed)} folder trong output, bỏ qua...")

    failed_folders = []
    success_count = 0

    print(f"Bắt đầu xử lý {len(folders)} thư mục tài liệu...")

    with open(output_file, 'a', encoding='utf-8') as outfile:
        for folder_name in folders:
            
            # ✅ Bỏ qua folder đã xử lý thành công
            if folder_name in processed:
                print(f"⏩ Bỏ qua (đã có): {folder_name}")
                continue

            folder_path = os.path.join(image_dir, folder_name)
            print(f"\n📂 Đang xử lý: {folder_name}")

            try:
                result = process_folder_with_ai(folder_path, folder_name)
            except Exception as e:
                print(f"   [🔥] Script bị crash ngang khi xử lý {folder_name}: {e}")
                result = None
                
            if result:
                outfile.write(json.dumps(result, ensure_ascii=False) + '\n')
                outfile.flush()  # ✅ Ghi ngay, không bị mất nếu crash
                success_count += 1
                print("   ✅ Trích xuất thành công!")
            else:
                failed_folders.append(folder_name)
                print("   ❌ Trích xuất thất bại!")

            time.sleep(5)

    # ✅ Ghi danh sách folder thất bại ra file
    if failed_folders:
        with open(failed_log, 'w', encoding='utf-8') as f:
            f.write('\n'.join(failed_folders))
        print(f"\n⚠️  {len(failed_folders)} folder thất bại, danh sách lưu tại: {failed_log}")
    
    print(f"\n{'='*40}")
    print(f"🎉 Hoàn tất! Thành công: {success_count}, Thất bại: {len(failed_folders)}")
    print(f"📄 Dữ liệu lưu tại: {output_file}")

if __name__ == "__main__":
    # 1. Lấy đường dẫn của thư mục chứa script hiện tại (tức là thư mục 'data-pipeline')
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Lùi lại 1 cấp để lấy đường dẫn thư mục gốc của dự án
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    
    # 3. Nối đường dẫn từ thư mục gốc vào thư mục data
    IMAGE_DIRECTORY = os.path.join(PROJECT_ROOT, "data", "image")
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_images_knowledge_base.jsonl")
    
    process_images_with_ai(IMAGE_DIRECTORY, OUTPUT_FILE)