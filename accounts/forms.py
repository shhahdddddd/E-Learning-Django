from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('', 'Sélectionnez un rôle'),
        ('etudiant', 'Étudiant'),
        ('enseignant', 'Enseignant'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label="Rôle",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    cv = forms.FileField(
        label="CV (PDF, max 2MB)",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'password1', 'password2', 'cv')