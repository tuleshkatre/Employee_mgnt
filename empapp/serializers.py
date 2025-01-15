from rest_framework import serializers
from .models import Employee , Attendance , Task , Post , User

class EmployeeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True) 

    class Meta:
        model = Employee
        fields = ['id', 'username', 'phone', 'email', 'first_name', 'last_name', 'image', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            username=validated_data.pop('username'),
            email=validated_data.pop('email'),
            first_name=validated_data.pop('first_name'),
            last_name=validated_data.pop('last_name'),
        )
        user.set_password(password)
        user.save()
        employee = Employee.objects.create(
            user=user, 
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            image=validated_data.get('image'),      
            phone=validated_data.pop('phone'),      
        )
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
        fields = ['employee' , 'title' , 'description' , 'deadline' , 'status']


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id' , 'title' , 'description']




