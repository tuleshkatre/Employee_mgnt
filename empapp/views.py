from django.shortcuts import render , redirect , get_object_or_404
from .forms import EmpCreate , TaskForm , AttendanceForm , PostForm , UpdateUserForm
from .models import Employee , Task , Attendance , CheckInOut , UserOTP , Post
from django.contrib.auth import authenticate , login as auth_login , logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.mail import send_mail
from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator
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
        password = request.POST.get('password')
        otp = request.POST.get('otp')
        user = User.objects.get(email = email)
        # Password-based login
        if email and password:
            user = authenticate(request, username=user.username, password=password)
            if user:
                auth_login(request, user)
                return redirect('read')
            else:
                return render(request, 'login.html', {'error': 'Invalid email or password.'})

        # OTP-based login
        if email and not otp:
            try:
                user = User.objects.filter(email=email).first() or Employee.objects.filter(email=email).first()
                if user:
                    generate_and_send_otp(user)
                    return render(request, 'otp_verify.html', {'email': email, 'message': f"OTP sent to your email :- {user.email}"})
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
                    return redirect('read')
                else:
                    return render(request, 'otp_verify.html', {'email': email, 'error': 'Invalid or expired OTP.'})
            except (User.DoesNotExist, Employee.DoesNotExist):
                return render(request, 'otp_verify.html', {'email': email, 'error': 'Invalid request.'})

    return render(request, 'login.html')

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
        
@login_required
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

@login_required
def like(request, id):
    if request.user.is_superuser:
        return redirect('read')
    
    post = get_object_or_404(Post, id=id)
    user = request.user

    if user in post.liked_by.all():
        post.liked_by.remove(user)
        post.likes -= 1
    else:
        post.liked_by.add(user)
        post.likes += 1
        if user in post.disliked_by.all():
            post.disliked_by.remove(user)
            post.dislikes -= 1

    post.save()
    page = request.POST.get('page', 1)
    return redirect(f'/show_post/?page={page}')

@login_required
def dis_like(request, id):
    if request.user.is_superuser:
        return redirect('read')
    
    post = get_object_or_404(Post, id=id)
    user = request.user

    if user in post.disliked_by.all():
        post.disliked_by.remove(user)
        post.dislikes -= 1
    else:
        post.disliked_by.add(user)
        post.dislikes += 1
        if user in post.liked_by.all():
            post.liked_by.remove(user)
            post.likes -= 1

    post.save()
    page = request.POST.get('page', 1)
    return redirect(f'/show_post/?page={page}')

@login_required
def show_post(request):
    if request.user.is_superuser:
        return redirect('read')

    all_posts = Post.objects.all()
    trending_posts = Post.objects.annotate(total_likes=Count('liked_by')).order_by('-total_likes')[:2]

    paginator = Paginator(all_posts, 2)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'show_post.html', {'page_obj': page_obj, 'tr_posts': trending_posts})

@login_required
def update_user(request, id):
    user_instance = Employee.objects.get(id = id) 
    if request.method == 'POST':
        emp_data = UpdateUserForm(data=request.POST , files=request.FILES ,instance = user_instance)
        if emp_data.is_valid():
            emp_data.save()
            return redirect('read')
    else:
        emp_data = UpdateUserForm(instance = user_instance)
    return render(request , 'update_user.html' , {'emp_data':emp_data})




# posts = Post.objects.annotate(
#     like_count=Count('liked_by'),
#     dislike_count=Count('disliked_by'),
#     total_likes_dislikes=F('like_count') + F('dislike_count')
# ).order_by('-total_likes_dislikes')[:2]

# from django.db.models import Count

# posts = Post.objects.annotate(
#     like_count=Count('liked_by'),
#     dislike_count=Count('disliked_by')
# ).order_by('-like_count', '-dislike_count')[:2] 





