from rest_framework import serializers
from .models import Employee , Attendance, Task, Post

class EmployeeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  

    class Meta:
        model = Employee
        fields = ['id', 'username', 'phone', 'email', 'first_name', 'last_name', 'image', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')  
        employee = Employee(**validated_data)  
        employee.set_password(password) 
        employee.save()
        return employee
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(required=False, write_only=True)
    otp = serializers.CharField(required=False, write_only=True)


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['employee' , 'date' , 'status']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['employee' , 'title', 'description', 'deadline' , 'status']

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id','title' , 'description']

