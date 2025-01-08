from rest_framework import serializers
from .models import Employee

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


