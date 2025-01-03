"""
URL configuration for empmanagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from empapp import views

urlpatterns = [
    
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('create/', views.emp_create, name='create'),
    path('login/', views.user_login, name='login'),
    path('read/', views.read, name='read'),
    path('create_task/', views.create_task, name='create_task'),
    path('task_list/', views.task_list, name='task_list'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('attendance/', views.attendance, name='attendance'),
    path('attendance_list/', views.attendance_list, name='attendance_list'),
    
    path('check_in/', views.check_in, name='check_in'),
    path('check_out/', views.check_out, name='check_out'),
    path('check_read/', views.check_read, name='check_read'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

