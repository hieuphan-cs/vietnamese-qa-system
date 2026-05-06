import os
import re
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

# =====================================================
# CONFIG
# =====================================================
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", ";", " ", ""]
)

# =====================================================
# CLEAN TEXT
# =====================================================
def clean_text(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# =====================================================
# SPLIT 1: LEGAL DOCUMENT
# Điều 1 / Chương I / Khoản 1
# =====================================================
def split_legal_structure(text):
    pattern = r'(?=(Chương\s+[IVXLC]+|Điều\s+\d+|Khoản\s+\d+|Mục\s+[IVXLC\d]+))'

    parts = re.split(pattern, text, flags=re.IGNORECASE)

    chunks = []
    current = ""

    for part in parts:
        part = part.strip()

        if not part:
            continue

        if re.match(
            r'^(Chương\s+[IVXLC]+|Điều\s+\d+|Khoản\s+\d+|Mục\s+[IVXLC\d]+)$',
            part,
            re.IGNORECASE
        ):
            if current:
                chunks.append(current.strip())
            current = part
        else:
            current += " " + part

    if current:
        chunks.append(current.strip())

    return chunks


# =====================================================
# SPLIT 2: BULLET LIST
# - abc
# - xyz
# =====================================================
def split_bullet_list(text):
    lines = text.split("\n")

    header_lines = []
    bullet_items = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("-") or line.startswith("•"):
            bullet_items.append(line)
        else:
            header_lines.append(line)

    header = "\n".join(header_lines[:2]).strip()

    chunks = []

    for item in bullet_items:
        if header:
            chunks.append(header + "\n" + item)
        else:
            chunks.append(item)

    return chunks


# =====================================================
# SPLIT 3: HEADING BLOCKS
# =====================================================
def split_heading_blocks(text):
    lines = text.split("\n")

    chunks = []
    current = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if (
            len(line) < 120 and
            line.isupper() and
            current
        ):
            chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        chunks.append("\n".join(current).strip())

    return chunks


# =====================================================
# FALLBACK SPLIT
# =====================================================
def recursive_split(chunks):
    final_chunks = []

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            sub_chunks = text_splitter.split_text(chunk)
            final_chunks.extend(sub_chunks)
        else:
            final_chunks.append(chunk)

    return final_chunks


# =====================================================
# DETECT YEAR
# =====================================================
def detect_year(text):
    m = re.search(r"(20\d{2})", text)
    return m.group(1) if m else None


# =====================================================
# DETECT DOC TYPE
# =====================================================
def detect_doc_type(category):
    category = category.lower()

    if "quyet" in category:
        return "quyet_dinh"

    if "quy_che" in category:
        return "quy_che"

    if "hoc_vu" in category:
        return "hoc_vu"

    return "general"


# =====================================================
# SMART CHUNK
# input của bạn là cleaned_knowledge_base.jsonl
# =====================================================
def smart_chunk(content, category):
    content = clean_text(content)

    # 1. Legal docs
    if re.search(r"(Điều\s+\d+|Chương\s+[IVXLC]+|Khoản\s+\d+)", content, re.IGNORECASE):
        chunks = split_legal_structure(content)

    # 2. Bullet docs
    elif "\n-" in content or "\n•" in content:
        chunks = split_bullet_list(content)

    # 3. Heading docs
    elif content[:200].upper() == content[:200]:
        chunks = split_heading_blocks(content)

    # 4. fallback
    else:
        chunks = [content]

    return recursive_split(chunks)


# =====================================================
# MAIN
# =====================================================
def create_chunks(input_filepath, output_filepath):
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    total_chunks = 0

    print(f"Đọc dữ liệu từ: {input_filepath}")

    with open(input_filepath, "r", encoding="utf-8") as infile, \
         open(output_filepath, "a", encoding="utf-8") as outfile:

        for line in infile:
            if not line.strip():
                continue

            doc = json.loads(line)

            content = doc.get("content", "")
            if not content:
                continue

            category = doc.get("category", "")

            chunks = smart_chunk(content, category)

            for i, chunk_text in enumerate(chunks):
                chunk_doc = {
                    "source": doc.get("source", ""),
                    "source_url": doc.get("source_url", ""),
                    "title": doc.get("title", ""),
                    "category": category,
                    "chunk_id": f"{doc.get('title','doc')}_{i}",
                    "content": chunk_text,
                    "metadata": {
                        **doc.get("metadata", {}),
                        "doc_type": detect_doc_type(category),
                        "year": detect_year(chunk_text),
                        "length": len(chunk_text)
                    }
                }

                outfile.write(
                    json.dumps(chunk_doc, ensure_ascii=False) + "\n"
                )

                total_chunks += 1

    print("-" * 40)
    print(f"Hoàn tất! Tổng số chunks: {total_chunks}")
    print(f"Lưu tại: {output_filepath}")


# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

    INPUT_FILE = os.path.join(
        PROJECT_ROOT,
        "data",
        "processed",
        "cleaned_knowledge_base.jsonl"
    )

    OUTPUT_FILE = os.path.join(
        PROJECT_ROOT,
        "data",
        "processed",
        "chunked_knowledge_base_1.jsonl"
    )

    create_chunks(INPUT_FILE, OUTPUT_FILE)