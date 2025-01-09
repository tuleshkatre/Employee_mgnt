from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from django.urls import path
from . import api
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # JWT token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Custom API endpoints
    path('api/create_employee/', api.create_employee, name='create_employee'),
    path('api/login/', api.login, name='login'),
    path('api/logout/', api.logout_view, name='logout'),
    path('api/update/<int:id>/', api.update_employee, name='update'),
    path('api/emp_read/<int:id>/', api.emp_read, name='emp_read'),
    path('api/emp_read/', api.emp_read, name='emp_read'),
    path('api/attendance/', api.attendance_view, name='attendance_view'),
    path('api/tasks/', api.task_view, name='task_view'),
    path('api/posts/', api.post_view, name='post_view'),
    path('api/check_in/', api.check_in, name='check_in'),
    path('api/check_out/', api.check_out, name='check_out'),
    path('api/like_dislike/<int:id>/<str:action>/', api.like_dislike, name='like_dislike'),
    path('api/tranding_post/', api.show_post, name='tranding_post'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


