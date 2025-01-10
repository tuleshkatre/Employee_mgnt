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
from .serializers import EmployeeSerializer, LoginSerializer , AttendanceSerializer , TaskSerializer
from .models import UserOTP, Employee , Attendance , Task
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied , ValidationError


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
                return ValidationError('Employee not found')
            
            date = serializer.validated_data['date']
            if Attendance.objects.filter(employee=employee, date=date).exists():
                return ValidationError('Attendance for this date already exists.')

            serializer.save(employee=employee)
            return Response({'message': 'Attendance marked successfully.'}, status=status.HTTP_201_CREATED)


from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework import status

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
            raise ValidationError('Employee not found.')

        date = serializer.validated_data['date']
        if Attendance.objects.filter(employee=employee, date=date).exists():
            raise ValidationError('Attendance for this date already exists.')

        # Save the attendance record
        serializer.save(employee=employee)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data['message'] = 'Attendance marked successfully.'
        return response


from rest_framework.views import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied

class EmployeeAttendanceAPIView(generics.ListCreateAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied('Only admins can manage attendance.')
        return Attendance.objects.all()

    def create(self, request, *args, **kwargs):
        employee_id = request.data.get('employee')
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            raise ValidationError('Employee not found.')

        date = request.data.get('date')
        if Attendance.objects.filter(employee=employee, date=date).exists():
            raise ValidationError('Attendance for this date already exists.')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(employee=employee)

        return Response({'message': 'Attendance marked successfully.'}, status=status.HTTP_201_CREATED)



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
    

class EmployeeTaskAPIView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer





