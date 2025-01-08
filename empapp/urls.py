from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from .api import create_employee , login

urlpatterns = [
    
    path('emp_create/', create_employee ,name='emp_create'),
    path('api_login/', login, name='api_login'),
    # path('read/', views.read, name='read'),
    # path('user_logout/', views.user_logout, name='user_logout'),
    # path('check_in/', views.check_in, name='check_in'),
    # path('check_out/', views.check_out, name='check_out'),
    # path('like/<int:id>/', views.like, name='like'),
    # path('dis_like/<int:id>/', views.dis_like, name='dis_like'),
    # path('show_post/', views.show_post, name='show_post'),
    # path('update/<int:id>/', views.update_user, name='update'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




