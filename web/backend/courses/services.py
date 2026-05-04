from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import pandas as pd
from django.db import transaction
from .models import Course, User, Enrollment

def get_all_courses():
    return Course.objects.all()

def create_course(data: dict) -> dict:
    code = data.get('code')
    name = data.get('name')

    if Course.objects.filter(code=code).exists():
        return {
            "success": False,
            "message": f"Mã môn học '{code}' đã tồn tại.",
            "data": None
        }

    try:
        course = Course.objects.create(code=code, name=name)
        return {
            "success": True,
            "message": "Tạo môn học thành công.",
            "data": course
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Có lỗi xảy ra: {str(e)}",
            "data": None
        }

def get_course_detail(course_id: int) -> Course:
    return Course.objects.prefetch_related('teachers', 'enrollment_set__student').filter(id=course_id).first()

def update_course(course_id: int, data: dict) -> dict:
    course = get_course_detail(course_id)
    if not course:
        return {
            "success": False,
            "message": "Môn học không tồn tại.",
            "data": None
        }
    
    new_code = data.get('code')
    if new_code and new_code != course.code:
        if Course.objects.filter(code=new_code).exists():
            return {
                "success": False,
                "message": f"Mã môn học '{new_code}' đã bị trùng với môn khác.",
                "data": None
            }
        course.code = new_code
        
    if 'name' in data:
        course.name = data['name']
    
    course.save()
    return {
        "success": True,
        "message": "Cập nhật thông tin môn học thành công.",
        "data": course
    }

def delete_course(course_id: int) -> dict:
    course = get_course_detail(course_id)
    if not course:
        return {
                "success": False,
                "message": "Môn học không tồn tại hoặc đã bị xóa.",
                "data": None
            }
        
    course_title = course.name
    course.delete()
    return {
            "success": True,
            "message": f"Đã xóa tài liệu {course_title} thành công.",
            "data": None
        }

def add_student_to_course(course_id: int, student_id: int) -> dict:
    course = Course.objects.filter(id=course_id).first()
    student = User.objects.filter(id=student_id).first()

    if not course:
        return {"success": False, "message": "Môn học không tồn tại", "data": None}
    if not student:
        return {"success": False, "message": "Sinh viên không tồn tại", "data": None}
    
    if student.role != User.Role.STUDENT:
        return {
            "success": False,
            "message": "User này không phải là sinh viên",
            "data": None
        }
    
    enrollment, created = Enrollment.objects.get_or_create(
        course=course, 
        student=student
    )
    
    message = "Đăng ký môn cho sinh viên thành công." if created else "Sinh viên này đã đăng ký môn học từ trước."
    return {
        "success": True,
        "message": message,
        "data": enrollment
    }

def remove_student_from_course(course_id: int, student_id: int):
    deleted_count, _ = Enrollment.objects.filter(course_id=course_id, student_id=student_id).delete()
    if deleted_count > 0:
        return {"success": True, "message": "Đã xóa sinh viên khỏi môn học.", "data": None}
    return {"success": False, "message": "Sinh viên chưa đăng ký môn này.", "data": None}

def add_teacher_to_course(course_id: int, teacher_id: int) -> dict:
    course = Course.objects.filter(id=course_id).first()
    teacher = User.objects.filter(id=teacher_id).first()

    if not course:
        return {"success": False, "message": "Môn học không tồn tại", "data": None}
    
    if not teacher:
         return {"success": False, "message": "User không tồn tại", "data": None}
         
    if not teacher.is_teacher:
        return {"success": False, "message": "User này không phải là giáo viên", "data": None}
         
    course.teachers.add(teacher)
    
    return {
        "success": True,
        "message": f"Đã thêm giáo viên {teacher.email} vào môn học.",
        "data": course
    }
    
def remove_teacher_from_course(course_id: int, teacher_id: int) -> dict:
    course = Course.objects.filter(id=course_id).first()
    teacher = User.objects.filter(id=teacher_id).first()

    if not course:
        return {"success": False, "message": "Môn học không tồn tại.", "data": None}
    
    if not teacher:
        return {"success": False, "message": "User không tồn tại.", "data": None}

    if not course.teachers.filter(id=teacher_id).exists():
        return {
            "success": False, 
            "message": "Giáo viên này hiện không dạy môn học này.", 
            "data": None
        }

    course.teachers.remove(teacher)
    
    return {
        "success": True,
        "message": f"Đã xóa giáo viên {teacher.email} khỏi môn học.",
        "data": None
    }
    
def get_courses_by_teacher(teacher_id: int):
    return Course.objects.filter(teachers__id=teacher_id)

def get_courses_by_student(student_id: int):
    return Enrollment.objects.filter(student_id=student_id).select_related('course')

def update_student_grade(course_id: int, student_id: int, grade: float) -> dict:
    enrollment = Enrollment.objects.filter(course_id=course_id, student_id=student_id).first()
    
    if enrollment:
        enrollment.grade = grade
        enrollment.save()
        return {
            "success": True,
            "message": "Cập nhật điểm cho sinh viên thành công.",
            "data": enrollment
        }
        
    return {
        "success": False,
        "message": "Không tìm thấy thông tin đăng ký của sinh viên trong môn học này.",
        "data": None
    }

def import_courses_from_excel(file) -> dict:
    try:
        df = pd.read_excel(file, engine='openpyxl')
        df = df.replace({pd.NA: None}) 
    except Exception as e:
        return {"success": False, "message": "Định dạng file không hợp lệ hoặc không thể đọc.", "data": None}

    success_count = 0
    errors = []

    for index, row in df.iterrows():
        row_number = index + 2 

        code = row.get('Code')
        name = row.get('Name')

        if not code or str(code).strip() == "":
            errors.append(f"Dòng {row_number}: Bỏ qua vì thiếu mã môn học (code).")
            continue
            
        if not name or str(name).strip() == "":
            errors.append(f"Dòng {row_number}: Bỏ qua vì thiếu tên môn học (name).")
            continue

        clean_code = str(code).strip()
        if Course.objects.filter(code=clean_code).exists():
            errors.append(f"Dòng {row_number}: Mã môn học '{clean_code}' đã tồn tại.")
            continue

        try:
            Course.objects.create(
                code=clean_code,
                name=str(name).strip(),
            )
            success_count += 1
        except Exception as e:
            errors.append(f"Dòng {row_number}: Lỗi khi lưu DB - {str(e)}")

    if success_count == 0 and errors:
        return {
            "success": False,
            "message": "Không có môn học nào được import thành công.",
            "data": {"errors": errors}
        }

    return {
        "success": True,
        "message": f"Import thành công {success_count} môn học.",
        "data": {"errors": errors} if errors else None
    }

def import_members_to_course(file) -> dict:
    try:
        df = pd.read_excel(file, engine='openpyxl')
        df = df.replace({pd.NA: None}) 
    except Exception as e:
        return {"success": False, "message": "Định dạng file không hợp lệ.", "data": None}

    success_count = 0
    errors = []
    
    course_cache = {}

    for index, row in df.iterrows():
        row_number = index + 2 
        email = row.get('Email')
        course_code = row.get('Course Code') 

        if not email or str(email).strip() == "":
            errors.append(f"Dòng {row_number}: Bỏ qua vì thiếu email.")
            continue
            
        if not course_code or str(course_code).strip() == "":
            errors.append(f"Dòng {row_number}: Bỏ qua vì thiếu mã môn học (course_code).")
            continue

        clean_email = str(email).strip()
        clean_course_code = str(course_code).strip()

        if clean_course_code not in course_cache:
            course = Course.objects.filter(code=clean_course_code).first()
            course_cache[clean_course_code] = course
            
        course = course_cache[clean_course_code]
        
        if not course:
            errors.append(f"Dòng {row_number}: Môn học có mã '{clean_course_code}' không tồn tại.")
            continue

        user = User.objects.filter(email=clean_email).first()
        if not user:
            errors.append(f"Dòng {row_number}: Không tìm thấy user '{clean_email}'.")
            continue

        if user.is_student:
            enrollment, created = Enrollment.objects.get_or_create(course=course, student=user)
            if not created:
                errors.append(f"Dòng {row_number}: Sinh viên '{clean_email}' đã có trong môn '{clean_course_code}'.")
            else:
                success_count += 1
                
        elif user.is_teacher:
            if course.teachers.filter(id=user.id).exists():
                errors.append(f"Dòng {row_number}: Giáo viên '{clean_email}' đã dạy môn '{clean_course_code}'.")
            else:
                course.teachers.add(user)
                success_count += 1
                
        else:
            errors.append(f"Dòng {row_number}: '{clean_email}' là Admin, không thể thêm vào lớp học.")

    if success_count == 0 and errors:
        return {
            "success": False,
            "message": "Không có thành viên nào được thêm thành công.",
            "data": {"errors": errors}
        }

    return {
        "success": True,
        "message": f"Đã thêm thành công {success_count} thành viên vào các môn học.",
        "data": {"errors": errors} if errors else None
    }