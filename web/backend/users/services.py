import re
import pandas as pd
from google.oauth2 import id_token
from google.auth.transport import requests
from django.utils import timezone
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from courses.models import Enrollment
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def verify_google_token(token: str):
    # Xác thực token với Google và trả về thông tin user
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), settings.GOOGLE_CLIENT_ID, clock_skew_in_seconds=10
        )
        return idinfo
    except Exception as e:
        return None

def get_or_create_google_user(idinfo: dict):
    # Lấy hoặc tạo mới User từ dữ liệu Google cung cấp
    email = idinfo['email']
    name = idinfo.get('name', '')
    avatar = idinfo.get('picture', '')

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'name': name,
            'avatar': avatar,
            'is_active': True,
        }
    )
    
    if not created:
        user.name = name
        user.avatar = avatar
        user.last_login = timezone.now()
        user.save(update_fields=["name", "avatar", "last_login"])
        
    return user

def get_user_by_id(user_id):
    return get_object_or_404(User, id=user_id)

def generate_tokens_for_user(user):
    # Tạo cặp Access & Refresh Token cho User
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
    
# Quản lý user
def generate_user_code(role: str) -> str:
    prefix_map = {
        "STUDENT": "SV",
        "TEACHER": "GV",
        "ADMIN": "AD"
    }

    prefix = prefix_map.get(role, "US")

    users = User.objects.filter(user_code__startswith=prefix)

    max_number = 0
    for u in users:
        match = re.search(rf"{prefix}(\d+)", u.user_code or "")
        if match:
            num = int(match.group(1))
            max_number = max(max_number, num)

    return f"{prefix}{max_number + 1:03d}"

def get_all_users(role: str = None):
    queryset = User.objects.all().order_by('-created_at')
    if role:
        queryset = queryset.filter(role=role)
    return queryset

def create_user_service(validated_data: dict):
    try:
        validated_data['user_code'] = generate_user_code(validated_data['role'])
        
        user = User(**validated_data)
        user.set_unusable_password() 
        user.save()
        
        return {
            "success": True,
            "message": "Tạo mới người dùng thành công!",
            "data": user
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Không thể tạo người dùng: {str(e)}",
            "data": None
        }

def update_user_service(user_instance, validated_data: dict):
    try:
        # 1. Lưu lại role cũ trước khi cập nhật
        old_role = user_instance.role
        new_role = validated_data.get('role', old_role)

        # 2. Cập nhật các trường dữ liệu mới
        for attr, value in validated_data.items():
            setattr(user_instance, attr, value)
        
        # 3. XỬ LÝ ĐẶC BIỆT NẾU ROLE BỊ THAY ĐỔI
        if old_role != new_role:
            # Tạo lại user_code mới (VD: từ SV... thành GV...)
            user_instance.user_code = generate_user_code(new_role)

            # Dọn dẹp dữ liệu khóa ngoại cũ để tránh lỗi CSDL
            if old_role == 'STUDENT':
                # Nếu trước đó là học sinh -> Xóa lịch sử học
                Enrollment.objects.filter(student=user_instance).delete()
            elif old_role == 'TEACHER':
                # Nếu trước đó là giáo viên -> Xóa lịch sử dạy
                user_instance.teaching_courses.clear()
        
        # 4. Lưu vào CSDL
        user_instance.save()
        
        return {
            "success": True,
            "message": "Cập nhật thông tin thành công!",
            "data": user_instance
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi khi cập nhật: {str(e)}",
            "data": None
        }

def delete_user_service(user_instance):
    try:
        user_instance.delete()
        return {
            "success": True,
            "message": "Đã xóa người dùng khỏi hệ thống.",
            "data": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Không thể xóa người dùng này.",
            "data": None
        }

def import_users_from_excel(file) -> dict:
    try:
        df = pd.read_excel(file, engine='openpyxl')
        df = df.replace({pd.NA: None}) 
    except Exception as e:
        return {"success": False, "message": "Định dạng file không hợp lệ.", "data": None}

    success_count = 0
    errors = []

    for index, row in df.iterrows():
        row_number = index + 2 

        email = row.get('Email')
        name = row.get('Name')
        role = row.get('Role', User.Role.STUDENT)
        user_code = generate_user_code(role)

        if not email:
            errors.append(f"Dòng {row_number}: Thiếu email.")
            continue
        if role not in User.Role.values:
            errors.append(f"Dòng {row_number}: Role '{role}' không hợp lệ.")
            continue
        if User.objects.filter(email=email).exists():
            errors.append(f"Dòng {row_number}: Email '{email}' đã tồn tại.")
            continue

        try:
            user = User(
                email=email,
                name=name if name else "",
                role=role,
                user_code=user_code
            )
            user.set_unusable_password() 
            user.save()
            success_count += 1
        except Exception as e:
            errors.append(f"Dòng {row_number}: Lỗi lưu db - {str(e)}")

    if success_count == 0 and errors:
        return {"success": False, "message": "Không có user nào import thành công.", "data": {"errors": errors}}

    return {"success": True, "message": f"Import thành công {success_count} user.", "data": {"errors": errors} if errors else None}