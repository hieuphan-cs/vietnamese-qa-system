from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (GoogleLoginView, UserMeView, UserListView, UserDetailView, ImportUserExcelView,UserCoursesView,ImportCourseExcelView, ImportMemberCourseExcelView
)

urlpatterns = [
    # Login
    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('auth/me/', UserMeView.as_view(), name='user_me'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Import Excel
    path('import-excel/', ImportUserExcelView.as_view(), name='import_users_excel'), 
    # GET toàn bộ user + POST thủ công
    path('', UserListView.as_view(), name='users_view'),
    # GET + PUT + DELETE 1 user cụ thể
    path('<int:user_id>/', UserDetailView.as_view(), name='users_detail'),
    
    path('import/', ImportUserExcelView.as_view(), name='import-users'),

    path('<int:user_id>/courses/', UserCoursesView.as_view(), name='user_courses'),

    path('import-courses/', ImportCourseExcelView.as_view(), name='import_courses_excel'),
    path('import-members/', ImportMemberCourseExcelView.as_view(), name='import_members_excel'),
]