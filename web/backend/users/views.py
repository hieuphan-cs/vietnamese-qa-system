import pandas as pd
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.conf import settings
from .serializers import GoogleAuthSerializer, UserProfileSerializer, UserListDetailSerializer, UserCreateUpdateSerializer
from . import services

User = get_user_model()

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        print("CLIENT_ID:", settings.GOOGLE_CLIENT_ID)
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. Gọi Service để verify token
        token = serializer.validated_data['token']
        idinfo = services.verify_google_token(token)
        
        if not idinfo:
            return Response({"error": "Invalid Google Token"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Gọi Service để xử lý User
        user = services.get_or_create_google_user(idinfo)

        # 3. Tạo Token
        tokens = services.generate_tokens_for_user(user)
        
        return Response(tokens, status=status.HTTP_200_OK)
    
class UserListView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        #Lấy danh sách User (?role=student hoặc ?role=teacher)
        role_filter = request.query_params.get('role', None)
        users = services.get_all_users(role=role_filter)
        serializer = UserListDetailSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not getattr(request.user, 'is_admin', False):
            return Response({
                "success": False,
                "message": "Bạn không có quyền thực hiện hành động này!",
                "data": None,
                "errors": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = UserCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            result = services.create_user_service(serializer.validated_data)
            
            if result["success"]:
                result["data"] = UserListDetailSerializer(result["data"]).data
                return Response(result, status=status.HTTP_201_CREATED)
            
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": False,
            "message": "Dữ liệu không hợp lệ, vui lòng kiểm tra lại.",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, user_id):
        return get_object_or_404(User, id=user_id)

    def get(self, request, user_id):
        user = self.get_object(user_id)
        serializer = UserListDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        user = self.get_object(user_id)
        if not getattr(request.user, 'is_admin', False):
            return Response(
                {"message": "Bạn không có quyền này!"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = UserCreateUpdateSerializer(user, data=request.data, partial=True) 
        if serializer.is_valid():
            result = services.update_user_service(user, serializer.validated_data)
            
            if result["success"]:
                result["data"] = UserListDetailSerializer(result["data"]).data
                return Response(result, status=status.HTTP_200_OK)
            
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response({
                "success": False,
                "message": "Dữ liệu không hợp lệ, vui lòng kiểm tra lại.",
                "data": None,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        user = self.get_object(user_id)
        if not getattr(request.user, 'is_admin', False):
            return Response(
                {"message": "Bạn không có quyền này!"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        result = services.delete_user_service(user)
        
        status_code = status.HTTP_200_OK if result["success"] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)
    
class UserMeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

class ImportUserExcelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not getattr(request.user, 'is_admin', False):
            return Response({
                "success": False,
                "message": "Bạn không có quyền thực hiện hành động này!"
            }, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Vui lòng đính kèm file Excel."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            df = pd.read_excel(file)
            
            # CHUẨN HOÁ CỘT EXCEL: Đổi tất cả tiêu đề cột sang chữ thường và xóa khoảng trắng dư
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            # LƯU Ý: Đổi 'username' thành 'name' cho khớp đúng file Excel và Database của bạn
            required_columns = ['name', 'email', 'role']
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                return Response(
                    {"error": f"File thiếu các cột: {', '.join(missing_cols)}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            created_count = 0
            updated_count = 0
            
            for index, row in df.iterrows():
                email = str(row['email']).strip()
                name = str(row['name']).strip() # Lấy cột Name trong file excel
                role = str(row['role']).strip().upper() if pd.notna(row['role']) else 'STUDENT'
                
                if not email or email == 'nan':
                    continue

                user, created = User.objects.update_or_create(
                    email=email,
                    defaults={
                        'name': name, # Đã sửa thành key 'name' của Database
                        'role': role
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            return Response({
                "message": f"Import thành công! Đã thêm {created_count} user mới, cập nhật {updated_count} user."
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"Đã xảy ra lỗi khi xử lý file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserCoursesView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user_id):
        return get_object_or_404(User, id=user_id)

    def get(self, request, user_id):
        user = self.get_object(user_id)
        try:
            if user.role == User.Role.TEACHER:
                courses = user.teaching_courses.all()
            elif user.role == User.Role.STUDENT:
                courses = user.enrolled_courses.all()
            else:
                courses = [] 

            course_ids = list(courses.values_list('id', flat=True)) if courses else []
            return Response(course_ids, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"Lỗi lấy dữ liệu môn học: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, user_id):
        if not getattr(request.user, 'is_admin', False):
            return Response({"message": "Bạn không có quyền phân công môn học!"}, status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object(user_id)
        course_ids = request.data.get('course_ids', [])
        
        try:
            if user.role == User.Role.TEACHER:
                user.teaching_courses.set(course_ids)
            elif user.role == User.Role.STUDENT:
                user.enrolled_courses.set(course_ids, clear=True)
            else:
                return Response({"message": "Không thể phân công môn học cho Admin!"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({"message": "Cập nhật phân công môn học thành công!"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"Lỗi khi cập nhật môn học: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # MỚI: API IMPORT MÔN HỌC (Đọc cột Code, Name)
class ImportCourseExcelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not getattr(request.user, 'is_admin', False):
            return Response({"message": "Không có quyền!"}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file: return Response({"error": "Vui lòng đính kèm file Excel."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            df = pd.read_excel(file)
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            if 'code' not in df.columns or 'name' not in df.columns:
                return Response({"error": "File thiếu cột 'Code' hoặc 'Name'."}, status=status.HTTP_400_BAD_REQUEST)

            created_count = 0
            for index, row in df.iterrows():
                code = str(row['code']).strip()
                name = str(row['name']).strip()
                if not code or code == 'nan': continue

                # Nhớ import Course model ở đầu file views.py
                from courses.models import Course 
                _, created = Course.objects.update_or_create(code=code, defaults={'name': name})
                if created: created_count += 1
            
            return Response({"message": f"Import thành công! Đã thêm mới/cập nhật {created_count} môn học."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Lỗi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# MỚI: API IMPORT PHÂN CÔNG (Đọc cột Email, Course Code)
class ImportMemberCourseExcelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not getattr(request.user, 'is_admin', False):
            return Response({"message": "Không có quyền!"}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file: return Response({"error": "Vui lòng đính kèm file Excel."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            df = pd.read_excel(file)
            # Chuẩn hoá cột: chữ thường, biến khoảng trắng thành dấu gạch dưới (course code -> course_code)
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            if 'email' not in df.columns or 'course_code' not in df.columns:
                return Response({"error": "File thiếu cột 'Email' hoặc 'Course Code'."}, status=status.HTTP_400_BAD_REQUEST)

            success_count = 0
            from courses.models import Course
            for index, row in df.iterrows():
                email = str(row['email']).strip()
                course_code = str(row['course_code']).strip()
                if not email or email == 'nan' or not course_code or course_code == 'nan': continue

                try:
                    user = User.objects.get(email=email)
                    course = Course.objects.get(code=course_code)
                    
                    if user.role == User.Role.TEACHER:
                        user.teaching_courses.add(course)
                        success_count += 1
                    elif user.role == User.Role.STUDENT:
                        user.enrolled_courses.add(course)
                        success_count += 1
                except:
                    continue # Bỏ qua nếu email hoặc mã môn không tồn tại trong DB
            
            return Response({"message": f"Import thành công! Đã phân công {success_count} lượt vào hệ thống."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Lỗi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)