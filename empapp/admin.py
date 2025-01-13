from django.contrib import admin
from .models import Employee, Task , Attendance , CheckInOut , UserOTP , Post

@admin.register(Employee)
class EmloyeeAdmin(admin.ModelAdmin):
    list_display = ['id','first_name', 'last_name','phone', 'email']

@admin.register(UserOTP)
class UserotpAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'otp_created_at']
    
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['employee' , 'title' , 'description' , 'deadline' , 'status']

@admin.register(Attendance)
class AttendenceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status']

@admin.register(CheckInOut)
class CheckInOutAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in' , 'check_out']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'employee', 'title', 'description' , 'created_at']



