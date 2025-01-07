from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta

class Employee(User):
    phone = models.CharField(max_length=15, unique=True)
    image = models.ImageField(default='dd.png', blank=True, null=True)

class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name= "otp_info",blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    def is_otp_valid(self):
        if self.otp_created_at:
            return (now() - self.otp_created_at).total_seconds() <= 600  
        return False

class Task(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateField()
    status = models.CharField(
        max_length=50, 
        choices=[('Pending', 'Pending'), ('Completed', 'Completed')],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default= now().date())
    status = models.CharField(max_length= 60 , choices=[('present', 'present'), ('absent', 'absent')] , default='present')

class CheckInOut(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=now().date())
    check_in = models.TimeField(blank=True, null=True)
    check_out = models.TimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.username} - {self.date}"

    def calculate_working_hours(self):
        if self.check_in and self.check_out:
            check_in_time = timedelta(
                hours=self.check_in.hour, minutes=self.check_in.minute, seconds=self.check_in.second
            )
            check_out_time = timedelta(
                hours=self.check_out.hour, minutes=self.check_out.minute, seconds=self.check_out.second
            )
            working_hours = check_out_time - check_in_time
            return working_hours
        return None

class Post(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    disliked_by = models.ManyToManyField(User, related_name='disliked_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.title





