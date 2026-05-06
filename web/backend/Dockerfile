FROM python:3.12-slim

# Ngăn Python tạo file .pyc và giúp log hiển thị ngay lập tức
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Cài đặt các gói hệ thống (Dependencies cho mysqlclient)
# Chúng ta gộp chung để đảm bảo tính nhất quán và giảm dung lượng image
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Chạy server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]