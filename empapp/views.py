from django.shortcuts import render, redirect
from .forms import EmpCreate, TaskForm , AttendanceForm 
from .models import Employee, Task , Attendance , CheckInOut, UserOTP
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.mail import send_mail
from django.contrib import messages
import random


def home(request):
    if request.user.is_authenticated:
        return redirect('read')
    return render(request , 'home.html')

def emp_create(request):
    if request.user.is_authenticated:
        return redirect('read')
    
    if request.method == 'POST':
        form = EmpCreate(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('create')
    else:
        form = EmpCreate()
    return render(request, 'Emp_create.html', {'form': form})

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

def user_login(request):
    if request.user.is_authenticated:
        return redirect('read')

    if request.method == 'POST':
        email = request.POST.get('email')
        otp = request.POST.get('otp')

        if email and not otp:
            try:
                user = User.objects.filter(email=email).first() or Employee.objects.filter(email=email).first()
                if user:
                    generate_and_send_otp(user)
                    return render(request, 'otp_verify.html', {'email': email, 'message': 'OTP sent to your email.'})
                else:
                    return render(request, 'login.html', {'error': 'No user found with this email.'})
            except Exception as e:
                return render(request, 'login.html', {'error': str(e)})

        if email and otp:
            try:
                user = User.objects.filter(email=email).first() or Employee.objects.filter(email=email).first()
                otp_info = user.otp_info
                if otp_info.is_otp_valid() and str(otp_info.otp) == otp:
                    auth_login(request, user) 
                    if isinstance(user, User) and user.is_superuser:
                        return redirect('read')
                    elif isinstance(user, Employee):
                        return redirect('read')
                else:
                    return render(request, 'otp_verify.html', {'email': email, 'error': 'Invalid or expired OTP.'})
            except (User.DoesNotExist, Employee.DoesNotExist, UserOTP.DoesNotExist):
                return render(request, 'otp_verify.html', {'email': email, 'error': 'Invalid request.'})

    return render(request, 'login.html')

# @login_required
# def read(request):
#     if request.user.is_superuser:

#         data = User.objects.filter(id=request.user.id)
#         att_list = Attendance.objects.all()
#         tasks = Task.objects.all()

#         if request.method == 'POST':
#             form = AttendenceForm(request.POST)
#             if form.is_valid():
#                 form.save()
#                 return redirect('login')
#         else:
#             form = AttendenceForm()

#         records = CheckInOut.objects.all()
#         for record in records:
#             record.working_hours = record.calculate_working_hours()

#         if request.method == 'POST':
#             task_form = TaskForm(request.POST)
#             if task_form.is_valid():
#                 task = form.save(commit=False)
#                 task.employee = Employee.objects.get(id = request.POST.get('employee'))
#                 task.save()
#                 return redirect('task_list')
#         else:
#             task_form = TaskForm()

#         return render(request, 'Admin_adashboard.html', {'data': data, 'tasks': tasks, 'form':form , 'att_list':att_list, 'records':records, 'task_form':task_form})

#     else:
#         data = Employee.objects.filter(id=request.user.id)
#         tasks = Task.objects.filter(employee=request.user)
#         return render(request, 'Employee_dashboard.html', {'data': data, 'tasks': tasks})
                  

@login_required
def read(request):
    if request.user.is_superuser:
        data = User.objects.filter(id=request.user.id)
        att_list = Attendance.objects.all()
        tasks = Task.objects.all()

        # Handle attendance form
        if request.method == 'POST':
            form = AttendanceForm(request.POST)
            if form.is_valid():
                date = form.cleaned_data['date']
                # Check if attendance already exists
                if Attendance.objects.filter(employee=request.user, date=date).exists():
                # if Attendance.objects.filter(employee=request.user, date=date).exists():
                    messages.error(request, 'Attendance for this date already exists.')
                else:
                    attendance = form.save(commit=False)
                    attendance.user = request.user
                    attendance.save()
                    messages.success(request, 'Attendance marked successfully.')
                    return redirect('read')
        else:
            form = AttendanceForm()

        # Handle task form
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

        # Calculate working hours
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
        return render(request, 'Employee_dashboard.html', {'data': data, 'tasks': tasks})

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def check_in(request):
    today = now().date()
    employee = Employee.objects.get(id = request.user.id)
    check_in_record, created = CheckInOut.objects.get_or_create(employee=employee, date=today)
    if not created and check_in_record.check_in is not None:
        return render(request, 'error.html', {'message': 'You have already checked in for today.'})
    check_in_record.check_in = now().time()
    check_in_record.save()

    return redirect('read')

@login_required
def check_out(request):
    today = now().date()
    employee = request.user
    try:
        check_in_record = CheckInOut.objects.get(employee=employee, date=today)
        if check_in_record.check_out is not None:
            return render(request, 'error.html', {'message': 'You have already checked out for today.'})
        check_in_record.check_out = now().time()
        check_in_record.save()
        return redirect('read')
    except CheckInOut.DoesNotExist:
        return render(request, 'error.html', {'message': 'You must check in before checking out.'})



