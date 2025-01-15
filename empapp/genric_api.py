import random
from rest_framework import generics
from .serializers import EmployeeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.mail import send_mail
from .serializers import EmployeeSerializer, LoginSerializer , AttendanceSerializer , TaskSerializer , PostSerializer
from .models import UserOTP, Employee , Attendance , Task , Post , CheckInOut
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied , ValidationError
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count
from rest_framework_simplejwt.exceptions import TokenError

# List and Create (GET and POST)
class EmployeeListCreateAPIView(generics.ListCreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


# Retrieve (GET by ID)
class EmployeeRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


# Update (PUT/PATCH by ID)
class EmployeeUpdateAPIView(generics.UpdateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


# delete (DELETE  by ID)
class EmployeeDeleteAPIView(generics.DestroyAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


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


class Login_view(APIView):
    def post(self, request):
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


class LogoutAPIView(APIView):
    def post(self, request):
        try:
            authorization_header = request.headers.get('Authorization')
            
            if authorization_header:
                refresh_token = request.data.get('refresh')
            else:
                return Response({'error': 'Refresh token is missing from the request.'}, status=400)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({'message': 'Successfully logged out.'}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=400)


class EmployeeAttendanceAPIView(generics.ListCreateAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied('Only admins can manage attendance.')
        return Attendance.objects.all()

    def perform_create(self, serializer):
            employee_id = self.request.data.get('employee')
            try:
                employee = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                raise ValidationError('Employee not found')
            
            date = serializer.validated_data['date']
            if Attendance.objects.filter(employee=employee, date=date).exists():
                raise ValidationError('Attendance for this date already exists.')

            serializer.save(employee=employee)
            return Response({'message': 'Attendance marked successfully.'}, status=status.HTTP_201_CREATED)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data['message'] = 'Attendance marked successfully.'
        return response


class EmployeeTaskAPIView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied('Only admins can manage task.')
        return Task.objects.all()

    def perform_create(self, serializer):
            # serializer = TaskSerializer(data=self.request.data)
            if serializer.is_valid():
                serializer.save()
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data['message'] = 'Task Assigned successfully.'
        return response


class EmployeePostAPIView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            raise PermissionDenied('You are not allowed to perform this task.')
        return Post.objects.all() 

    def perform_create(self, serializer):
        try:
            employee = Employee.objects.get(user=self.request.user)
        except Employee.DoesNotExist:
            raise ValidationError('Employee not found.')

        serializer.save(employee=employee)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data['message'] = 'Post created successfully.'
        return response


class EmployeeCheckinAPIView(APIView):

    def post(self, request, *args, **kwargs):
        today = now().date()
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee record not found'}, status=404)

        check_in_record, created = CheckInOut.objects.get_or_create(employee=employee, date=today)
        if not created and check_in_record.check_in is not None:
            return Response({'message': 'You have already checked in for today.'}, status=400)

        check_in_record.check_in = now().time()
        check_in_record.save()

        return Response({'message': 'Check-in successful'})


class EmployeeCheckoutAPIView(APIView):

    def post(self, request, *args, **kwargs):
        today = now().date()
        employee = self.request.user.employee

        try:
            check_in_record = CheckInOut.objects.get(employee=employee, date=today)
            if check_in_record.check_out is not None:
                return Response({'message': 'You have already checked out for today.'})
            check_in_record.check_out = now().time()
            check_in_record.save()
            return Response({'message': 'Check out successfull'})

        except CheckInOut.DoesNotExist:
            return Response({'message': 'You must check in before checking out.'})


class EmployeeLike_DislikeAPIView(APIView):
    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return Response({'message': 'Admins are not allowed to perform this action'}, status=status.HTTP_403_FORBIDDEN)

        post_id = kwargs.get('id')
        post = get_object_or_404(Post, id=post_id)
        user = self.request.user
        action = request.data.get('action')

        if action not in ['like', 'dislike']:
            return Response({'error': 'Invalid action. Must be "like" or "dislike".'}, status=status.HTTP_400_BAD_REQUEST)

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

        post.save()
        return Response({'message': message, 'likes': post.likes, 'dislikes': post.dislikes}, status=status.HTTP_200_OK)



##################################   show post api view with two types of view ==>  1) Gneric (ListCreateView)  2) ApiView       #################################



##  1) Gneric (ListCreateView)

class EmployeeShow_PostAPIView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def list(self, request, *args, **kwargs):
        all_posts = Post.objects.all()

        trending_posts = Post.objects.annotate(total_likes=Count('liked_by')).order_by('-total_likes')[:2]

        paginator = Paginator(all_posts, 2) 
        page_number = self.request.GET.get('page', 1)  
        page_obj = paginator.get_page(page_number)

        post_serializer = PostSerializer(page_obj, many=True)
        trending_serializer = PostSerializer(trending_posts, many=True)

        return Response({
            'posts': post_serializer.data, 
            'trending_posts': trending_serializer.data, 
            'total_pages': page_obj.paginator.num_pages, 
            'current_page': page_obj.number 
        })




## 2) ApiView    

# class EmployeeShow_PostAPIView(APIView):

#     def get(self , request , *args , **kwags):

#         if self.request.user.is_superuser:
#             raise PermissionDenied('Admins are not allowed to perform this action')
#         all_posts = Post.objects.all()
#         trending_posts = Post.objects.annotate(total_likes=Count('liked_by')).order_by('-total_likes')[:2]

#         paginator = Paginator(all_posts, 2) 
#         page_number = self.request.GET.get('page', 1)  
#         page_obj = paginator.get_page(page_number)

#         post_serializer = PostSerializer(page_obj, many=True)
#         trending_serializer = PostSerializer(trending_posts, many=True)

#         return Response({
#             'page_obj': post_serializer.data,
#             'trending_posts': trending_serializer.data,
#             'current_page': page_obj.number,
#             'total_pages': page_obj.paginator.num_pages
#         })





