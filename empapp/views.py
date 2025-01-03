from django.shortcuts import render, redirect
from .forms import EmpCreate, TaskForm , AttendenceForm , CheckInForm, CheckoutForm
from .models import Employee, Task , Attendance , CheckInOut, UserOTP
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.mail import send_mail
import random


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

def generate_and_send_otp(employee):
    otp = random.randint(100000, 999999)
    otp_info, _ = UserOTP.objects.get_or_create(employee=employee)
    otp_info.otp = otp
    otp_info.otp_created_at = now()
    otp_info.save()

    send_mail(
        'Your OTP Code',
        f'Your OTP is {otp}. It will expire in 10 minutes.',
        'noreply@example.com',
        [employee.email],
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
                employee = Employee.objects.get(email=email)
                generate_and_send_otp(employee)
                return render(request, 'otp_verify.html', {'email': email, 'message': 'OTP sent to your email.'})
            except Employee.DoesNotExist:
                return render(request, 'login.html', {'error': 'Employee with this email does not exist.'})

        if email and otp:
            try:
                employee = Employee.objects.get(email=email)
                otp_info = employee.otp_info
                if otp_info.is_otp_valid() and str(otp_info.otp) == otp:
                    auth_login(request, employee)  
                    return redirect('read')  
                else:
                    return render(request, 'otp_verify.html', {'email': email, 'error': 'Invalid or expired OTP.'})
            except (Employee.DoesNotExist, UserOTP.DoesNotExist):
                return render(request, 'otp_verify.html', {'email': email, 'error': 'Invalid request.'})

    return render(request, 'login.html')

@login_required
def read(request):
    data = Employee.objects.filter(id=request.user.id)
    return render(request, 'Emp_detail.html', {'data': data})

@login_required
def create_task(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            form = TaskForm(request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.employee = Employee.objects.get(id = request.POST.get('employee'))
                task.save()
                return redirect('task_list')
        else:
            form = TaskForm()
        return render(request, 'task_create.html', {'form': form})
    else:
        return redirect('login')
    
@login_required
def task_list(request):
    if request.user.is_superuser:
        tasks = Task.objects.all()  
    else:
        tasks = Task.objects.filter(employee=request.user) 
    return render(request, 'task_list.html', {'tasks': tasks})

def user_logout(request):
    logout(request)

    return redirect('login')

@login_required
def attendance(request):    
    if request.user.is_superuser:
        if request.method == 'POST':
            form = AttendenceForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('login')
        else:
            form = AttendenceForm()
        return render(request , 'attendence.html' , {'form':form})
    else:
        return render('login')
    
@login_required
def attendance_list(request):
    if request.user.is_superuser:
        data = Attendance.objects.all()
        return render(request, 'attendence_list.html', {'data':data})
    else:
        return redirect ('login')

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


@login_required
def check_read(request):
    records = CheckInOut.objects.all() #.order_by('-date')
    for record in records:
        record.working_hours = record.calculate_working_hours()

    return render(request, 'checkin_records.html', {'records': records})


# @login_required
# def check_read(request):
#     employee = request.user
#     records = CheckInOut.objects.filter(employee=employee) #.order_by('-date')
#     for record in records:
#         record.working_hours = record.calculate_working_hours()

#     return render(request, 'checkin_records.html', {'records': records})




