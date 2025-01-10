import random
from rest_framework.decorators import api_view, permission_classes 
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.mail import send_mail
from .serializers import EmployeeSerializer, LoginSerializer , AttendanceSerializer, TaskSerializer, PostSerializer
from .models import UserOTP, Employee ,  Attendance, Task, Post , CheckInOut
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.core.paginator import Paginator


# Function to generate and send OTP
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


# Function to generate tokens for a user
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# Create employee view
@api_view(['POST'])
def create_employee(request):
    serializer = EmployeeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View to list employees (requires authentication)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emp_read(request , id = None):
    if id:
        employees = Employee.objects.get(id= id)
        serializer = EmployeeSerializer(employees)

    else:
        employees = Employee.objects.all()
        serializer = EmployeeSerializer(employees, many=True)
    return Response(serializer.data)


# Update view
@api_view(['PUT'])
@permission_classes([IsAuthenticated]) 
def update_employee(request, id):
    try:
        employee = Employee.objects.get(id=id)
        
        serializer = EmployeeSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save() 
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)


# Delete view
@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
def delete_employee(request, id):
    try:
        employee = Employee.objects.get(id=id)
        employee.delete()
        return Response({'message': 'Delete successful!'})
      
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)


# Login view
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data.get('password')
        otp = serializer.validated_data.get('otp')

        # Password-based login
        if password:
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user:
                    auth_login(request, user)
                    tokens = get_tokens_for_user(user)
                    return Response({'message': 'Login successful!', 'tokens': tokens}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid email or password.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # OTP generation
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

        # OTP validation
        if otp:
            try:
                user = User.objects.filter(email=email).first() or Employee.objects.filter(email=email).first()
                otp_info = UserOTP.objects.get(user=user)
                if otp_info.is_otp_valid() and str(otp_info.otp) == otp:
                    auth_login(request, user)
                    tokens = get_tokens_for_user(user)
                    return Response({'message': 'OTP validated. Login successful!', 'tokens': tokens}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except UserOTP.DoesNotExist:
                return Response({'error': 'OTP not found for user.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Invalid input: Provide either password or OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# # @permission_classes([IsAuthenticated])
# def logout_view(request):
#     try:
#         refresh_token = request.headers.get('refresh').split(' ')[1] 
#         print(refresh_token)
        
#         token = RefreshToken(refresh_token)
#         token.blacklist()  

#         return JsonResponse({'message': 'Successfully logged out.'}, status=200)
    
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=400)


@api_view(['POST'])
def logout_view(request):
    try:
        authorization_header = request.headers.get('Authorization')
        
        if authorization_header:
            refresh_token = request.data.get('refresh')
        else:
            return JsonResponse({'error': 'Refresh token is missing from the request.'}, status=400)

        token = RefreshToken(refresh_token)
        token.blacklist()

        return JsonResponse({'message': 'Successfully logged out.'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def attendance_view(request):
    if not request.user.is_superuser:
        return Response({'error': 'Only admins can manage attendance.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        attendances = Attendance.objects.all()
        serializer = AttendanceSerializer(attendances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = AttendanceSerializer(data=request.data)
        if serializer.is_valid():
            employee_id = request.data.get('employee')
            try:
                employee = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                return Response({'error': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)

            date = serializer.validated_data['date']
            if Attendance.objects.filter(employee=employee, date=date).exists():
                return Response({'error': 'Attendance for this date already exists.'}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(employee=employee)
            return Response({'message': 'Attendance marked successfully.'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def task_view(request):
    if not request.user.is_superuser:
        return Response({'error': 'You do not have permission to manage tasks.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        attendances = Task.objects.all()
        serializer = TaskSerializer(attendances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Task assigned successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def post_view(request):
    if request.user.is_superuser:
        return Response({'error': 'Admins cannot manage posts.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        attendances = Post.objects.all()
        serializer = PostSerializer(attendances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            try:
                employee = Employee.objects.get(id=request.user.id)
            except Employee.DoesNotExist:
                return Response({'error': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)

            serializer.save(employee = employee)
            return Response({'message': 'Post created successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_in(request):
    today = now().date()
    employee = Employee.objects.get(id = request.user.id)
    check_in_record, created = CheckInOut.objects.get_or_create(employee=employee, date=today)
    if not created and check_in_record.check_in is not None:
        return Response({'message': 'You have already checked in for today.'})
    check_in_record.check_in = now().time()
    check_in_record.save()

    return Response({'message': 'Check in successfull'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_out(request):
    today = now().date()
    employee = request.user
    try:
        check_in_record = CheckInOut.objects.get(employee=employee, date=today)
        if check_in_record.check_out is not None:
            return Response({'message': 'You have already checked out for today.'})
        check_in_record.check_out = now().time()
        check_in_record.save()
        return Response({'message': 'Check out successfull'})

    except CheckInOut.DoesNotExist:
        return Response({'message': 'You must check in before checking out.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_dislike(request, id, action):
    if request.user.is_superuser:
        return Response({'message': 'Admins are not allowed to perform this action'}, status=status.HTTP_403_FORBIDDEN)

    post = get_object_or_404(Post, id=id)
    user = request.user

    if action == 'like':
        if user in post.liked_by.all():
            post.liked_by.remove(user)
            post.likes -= 1
            message = 'You unliked the post.'
        else:
            post.liked_by.add(user)
            post.likes += 1
            message = 'You liked the post.'
            if user in post.disliked_by.all():
                post.disliked_by.remove(user)
                post.dislikes -= 1
    elif action == 'dislike':
        if user in post.disliked_by.all():
            post.disliked_by.remove(user)
            post.dislikes -= 1
            message = 'You removed your dislike from the post.'
        else:
            post.disliked_by.add(user)
            post.dislikes += 1
            message = 'You disliked the post.'
            if user in post.liked_by.all():
                post.liked_by.remove(user)
                post.likes -= 1
    else:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    post.save()
    return Response({'message': message, 'likes': post.likes, 'dislikes': post.dislikes}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def show_post(request):
    if request.user.is_superuser:
        return Response({'message': 'Admins are not allowed to perform this action'}, status=status.HTTP_403_FORBIDDEN)

    all_posts = Post.objects.all()
    trending_posts = Post.objects.annotate(total_likes=Count('liked_by')).order_by('-total_likes')[:2]

    paginator = Paginator(all_posts, 2) 
    page_number = request.GET.get('page', 1)  
    page_obj = paginator.get_page(page_number)

    post_serializer = PostSerializer(page_obj, many=True)
    trending_serializer = PostSerializer(trending_posts, many=True)

    return Response({
        'page_obj': post_serializer.data,
        'trending_posts': trending_serializer.data,
        'current_page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages
    })






