from django import forms
from .models import Employee, Task , Attendance , Post

class EmpCreate(forms.ModelForm):
    password = forms.CharField()
    class Meta:
        model = Employee
        fields = ['username', 'phone', 'email', 'first_name', 'last_name', 'image', 'password']
        help_texts = { 'username': None, }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['employee', 'title', 'description', 'deadline', 'status']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'status']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description']

