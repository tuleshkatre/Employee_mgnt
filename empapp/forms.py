from django import forms
from .models import Employee, Task , Attendance , Post , User

class EmpCreate(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = Employee
        fields = ['username', 'phone', 'email', 'first_name', 'last_name', 'image', 'password']
        help_texts = {'username': None}

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
            email = self.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email is already registered.")
            return email

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['employee', 'title', 'description', 'deadline', 'status']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'status']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description']

class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['username', 'phone', 'email', 'first_name', 'last_name']
        help_texts = { 'username': None, }




