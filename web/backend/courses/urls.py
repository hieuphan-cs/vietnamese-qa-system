from django.urls import path
from . import views

urlpatterns = [

    # GET: Lấy danh sách | POST: Tạo mới môn học (+ giáo viên cho môn đó)
    # URL thực tế: /courses/
    path('', views.CourseListCreateView.as_view(), name='course-list-create'),
    
    # GET: Xem chi tiết | PUT: Sửa môn học | DELETE: Xóa môn học
    # URL thực tế: /courses/<id>/
    path('<int:course_id>/', views.CourseDetailView.as_view(), name='course-detail'),

    # POST: Thêm giáo viên dạy môn cụ thể | DELETE: Xóa giáo viên khỏi môn
    # URL thực tế: /courses/<id>/teachers/
    path('<int:course_id>/teachers/<int:teacher_id>', views.CourseTeacherView.as_view(), name='course-teachers'),

    # GET: Lấy các môn mà 1 giáo viên đang dạy
    # URL thực tế: /courses/teachers/<id>/
    path('teachers/<int:teacher_id>/', views.TeacherCoursesView.as_view(), name='teacher-courses'),
    
    path('import/', views.ImportCourseExcelView.as_view(), name='import-courses'),
    
    path('import/members/', views.ImportMembersExcelView.as_view(), name='global-members-import'),
    
    # POST: Thêm sinh viên vào môn | DELETE: Xóa sinh viên khỏi môn
    # URL thực tế: /courses/<id>/students/
    #path('<int:course_id>/students/<int:student_id>/', views.CourseStudentView.as_view(), name='course-students'),
    
    # GET: Lấy các môn mà 1 sinh viên đang học (kèm điểm số)
    # URL thực tế: /courses/students/<id>/
    #path('students/<int:student_id>/', views.StudentCoursesView.as_view(), name='student-courses'),
    
    # PUT: Cập nhật điểm cho sinh viên
    # URL thực tế: /courses/<id>/students/<id>/grade/
    #path('<int:course_id>/students/<int:student_id>/grade/', views.StudentGradeView.as_view(), name='student-grade'),
]