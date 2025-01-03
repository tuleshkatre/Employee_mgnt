from django import forms
from .models import Employee, Task , Attendance , CheckInOut

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

class AttendenceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'status']


