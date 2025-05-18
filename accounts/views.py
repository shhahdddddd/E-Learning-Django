from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django import forms
from .forms import CustomUserCreationForm
from django.urls import reverse
from django.utils.translation import gettext as _

class DirectPasswordResetForm(forms.Form):
    email = forms.EmailField(label=_('Email'), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(label=_('New password'), widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label=_('Confirm new password'), widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get('new_password1')
        pw2 = cleaned_data.get('new_password2')
        if pw1 and pw2 and pw1 != pw2:
            self.add_error('new_password2', _('Passwords do not match.'))
        return cleaned_data


def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)  # Note request.FILES for file upload
        if form.is_valid():
            user = form.save(commit=False)
            
            # Set role
            role = form.cleaned_data.get('role')
            user.is_teacher = (role == 'enseignant')
            user.is_student = (role == 'etudiant')
            
            # Handle CV upload for teachers
            if role == 'enseignant' and 'cv' in request.FILES:
                user.cv = request.FILES['cv']
            
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')


def direct_password_reset(request):
    User = get_user_model()
    if request.method == 'POST':
        form = DirectPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            new_password = form.cleaned_data['new_password1']
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                messages.success(request, _('Your password has been reset. Please log in with your new password.'))
                return redirect('login')
            except User.DoesNotExist:
                form.add_error('email', _('No user found with this email.'))
    else:
        form = DirectPasswordResetForm()
    return render(request, 'registration/direct_password_reset.html', {'form': form})