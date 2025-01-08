from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.mail import send_mail
import random
from .serializers import EmployeeSerializer, LoginSerializer
from .models import UserOTP, Employee ,Attendance, Task, Post, CheckInOut
from django.shortcuts import render , redirect
from .forms import TaskForm , AttendanceForm , PostForm 
from django.contrib import messages



def generate_and_send_otp(user):
    otp = random.randint(100000, 999999)
    otp_info, _ = UserOTP.objects.get_or_create(user=user)
    otp_info.otp = otp
    otp_info.otp_created_at = now()
    otp_info.save()

    send_mail(
        'Your OTP Code',
        f'Your OTP is {otp}. It will expire in 10 minutes.',
        'noreply@example.com',
        [user.email],
        fail_silently=False,
    )

@api_view(['POST'])
def create_employee(request):
    serializer = EmployeeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data.get('password')
        otp = serializer.validated_data.get('otp')

        if password:
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user:
                    auth_login(request, user)
                    return Response({'message': 'Login successful!'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid email or password.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if otp is None and password is None:
            try:
                user = User.objects.filter(email=email).first() or Employee.objects.filter(email=email).first()
                if user:
                    generate_and_send_otp(user)
                    return Response({'message': f"OTP sent to your email: {user.email}"}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'No user found with this email.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if otp:
            try:
                user = User.objects.filter(email=email).first() or Employee.objects.filter(email=email).first()
                otp_info = UserOTP.objects.get(user=user)
                if otp_info.is_otp_valid() and str(otp_info.otp) == otp:
                    auth_login(request, user)
                    return Response({'message': 'OTP validated. Login successful!'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except UserOTP.DoesNotExist:
                return Response({'error': 'OTP not found for user.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Invalid input: Provide either password or OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def read(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_superuser:
        data = User.objects.filter(id=request.user.id)
        att_list = Attendance.objects.all()
        tasks = Task.objects.all()

        if request.method == 'POST':
            form = AttendanceForm(request.POST)
            if form.is_valid():
                date = form.cleaned_data['date']
                employee_id = request.POST.get('employee') 
                employee = Employee.objects.get(id=employee_id) 
                existing_attendance = Attendance.objects.filter(employee=employee, date=date)
                if existing_attendance.exists():
                    messages.error(request, 'Attendance for this date already exists.')
                else:
                    attendance = form.save(commit=False)
                    attendance.employee = employee
                    attendance.save()
                    messages.success(request, 'Attendance marked successfully.')
                    return redirect('read')
        else:
            form = AttendanceForm()

        if request.method == 'POST':
            task_form = TaskForm(request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.employee = Employee.objects.get(id=request.POST.get('employee'))
                task.save()
                messages.success(request, 'Task assigned successfully.')
                return redirect('read')
        else:
            task_form = TaskForm()

        records = CheckInOut.objects.all()
        for record in records:
            record.working_hours = record.calculate_working_hours()

        return render(request, 'Admin_adashboard.html', {
            'data': data,
            'tasks': tasks,
            'form': form,
            'att_list': att_list,
            'records': records,
            'task_form': task_form,
        })

    else:
        data = Employee.objects.filter(id=request.user.id)
        tasks = Task.objects.filter(employee=request.user)
        all_posts = Post.objects.all()

        if request.method == 'POST':
                post = PostForm(request.POST)
                if post.is_valid():
                    posts = post.save(commit=False)
                    posts.employee = Employee.objects.get(id = request.user.id)
                    posts.save()
                    return redirect('read')
        else:
            post = PostForm()
        return render(request, 'Employee_dashboard.html', {'data': data, 'tasks': tasks , 'post':post , 'all_posts':all_posts})
        