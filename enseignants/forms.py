from django import forms
from .models import Formation, Course,UserProfile

class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = ['titre', 'description', 'prix']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['titre', 'td_file', 'tp_file', 'correction']
        labels = {
            'td_file': 'Fichier TD',
            'tp_file': 'Fichier TP',
            'correction': 'Correction'
        }
class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']