from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from . import services
from .serializers import CourseSerializer, EnrollmentSerializer
from config.permissions import IsAdmin

# Create your views here.

# 1. QUẢN LÝ MÔN HỌC (CRUD)
class CourseListCreateView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        user = request.user
        
        # 1. Nếu là Admin -> Lấy tất cả
        if user.is_admin:
            courses = services.get_all_courses()
            serializer = CourseSerializer(courses, many=True)
            
        # 2. Nếu là Teacher -> Lấy môn giáo viên đó dạy
        elif user.is_teacher:
            courses = services.get_courses_by_teacher(user.id)
            serializer = CourseSerializer(courses, many=True)
            
        # 3. Nếu là Student -> Lấy môn sinh viên đó đăng ký
        else:
            enrollments = services.get_courses_by_student(user.id)
            # Bóc tách lấy object Course từ Enrollment
            courses = [enrollment.course for enrollment in enrollments]
            serializer = CourseSerializer(courses, many=True)

        return Response({
            "success": True,
            "message": "Lấy danh sách khóa học thành công.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    def post(self, request):
        # Kiểm tra thêm quyền: Phải là Admin mới được tạo khóa học
        if not request.user.is_admin:
            return Response({
                "success": False,
                "message": "Bạn không có quyền tạo môn học.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        result = services.create_course(request.data)
        
        if not result['success']:
            return Response({"success": False, "message": result['message'], "data": None}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CourseSerializer(result['data'])
        return Response({"success": True, "message": result['message'], "data": serializer.data}, status=status.HTTP_201_CREATED)

class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        course = services.get_course_detail(course_id)
        if not course:
            return Response({"success": False, "message": "Môn học không tồn tại.", "data": None}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = CourseSerializer(course)
        return Response({"success": True, "message": "Thành công.", "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, course_id):
        if not request.user.is_admin:
            return Response({"success": False, "message": "Chỉ Admin mới được sửa môn học.", "data": None}, status=status.HTTP_403_FORBIDDEN)

        result = services.update_course(course_id, request.data)
        
        if not result['success']:
            return Response({"success": False, "message": result['message'], "data": None}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = CourseSerializer(result['data'])
        return Response({"success": True, "message": result['message'], "data": serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, course_id):
        if not request.user.is_admin:
            return Response({"success": False, "message": "Chỉ Admin mới được xóa môn học.", "data": None}, status=status.HTTP_403_FORBIDDEN)

        result = services.delete_course(course_id)
        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_404_NOT_FOUND
        return Response({"success": result['success'], "message": result['message'], "data": None}, status=status_code)

# 2. QUẢN LÝ SINH VIÊN TRONG MÔN HỌC

class CourseStudentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_id, student_id):
        if not request.user.is_admin:
            return Response({
                "success": False,
                "message": "Bạn không có quyền này!",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
            
        result = services.add_student_to_course(course_id, student_id)
        
        if not result['success']:
            return Response({
                "success": False,
                "message": result['message'],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = EnrollmentSerializer(result['data'])
        return Response({
            "success": True,
            "message": result['message'],
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, course_id, student_id):
        
        if not request.user.is_admin:
            return Response({
                "success": False,
                "message": "Bạn không có quyền này",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
            
        result = services.remove_student_from_course(course_id, student_id)
        
        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        return Response({
            "success": result['success'],
            "message": result['message'],
            "data": None
        }, status=status_code)

class StudentGradeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, course_id, student_id):
        # Chấm điểm: Cho phép cả Admin và Teacher
        if not (request.user.is_admin or request.user.is_teacher):
            return Response({
                "success": False,
                "message": "Chỉ Admin hoặc Giáo viên mới được cập nhật điểm.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        grade = request.data.get('grade')
        result = services.update_student_grade(course_id, student_id, grade)
        
        if not result['success']:
            return Response({"success": False, "message": result['message'], "data": None}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = EnrollmentSerializer(result['data'])
        return Response({"success": True, "message": result['message'], "data": serializer.data}, status=status.HTTP_200_OK)

# 3. QUẢN LÝ GIÁO VIÊN VÀ TRUY VẤN NGƯỢC

class CourseTeacherView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_id, teacher_id):
        
        if not request.user.is_admin:
            return Response({
                "success": False,
                "message": "Bạn không có quyền này",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        result = services.add_teacher_to_course(course_id, teacher_id)
        
        if not result['success']:
            return Response({
                "success": False,
                "message": result['message'],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = CourseSerializer(result['data'])
        return Response({
            "success": True,
            "message": result['message'],
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
        
    def delete(self, request, course_id, teacher_id):
        if not request.user.is_admin:
            return Response({
                "success": False,
                "message": "Bạn không có quyền này",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
            
        result = services.remove_teacher_from_course(course_id, teacher_id)
        
        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        
        return Response({
            "success": result['success'],
            "message": result['message'],
            "data": None
        }, status=status_code)
        
class TeacherCoursesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, teacher_id):
        courses = services.get_courses_by_teacher(teacher_id)
        serializer = CourseSerializer(courses, many=True)
        return Response({
            "success": True,
            "message": "Lấy danh sách môn học của giáo viên thành công.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

class StudentCoursesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, student_id):
        enrollments = services.get_courses_by_student(student_id)
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response({
            "success": True,
            "message": "Lấy danh sách môn học của sinh viên thành công.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
class ImportCourseExcelView(APIView):
    
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request):
       
        if not request.user.is_admin:
            return Response({
                "success": False,
                "message": "Chỉ Admin mới có quyền thực hiện chức năng này.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file or not file.name.endswith(('.xls', '.xlsx')):
            return Response({
                "success": False,
                "message": "Vui lòng đính kèm file định dạng Excel (.xls, .xlsx).",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        result = services.import_courses_from_excel(file)
        
        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)

class ImportMembersExcelView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_admin:
            return Response({
                "success": False,
                "message": "Chỉ Admin mới có quyền thực hiện chức năng này.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file or not file.name.endswith(('.xls', '.xlsx')):
            return Response({
                "success": False,
                "message": "Vui lòng đính kèm file định dạng Excel (.xls, .xlsx).",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Gọi logic mới
        result = services.import_members_to_course(file)
        
        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)