from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator

class EnseignantProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enseignant_profile'
    )
    cv = models.FileField(
        upload_to='enseignants/cvs/',
        validators=[FileExtensionValidator(['pdf'])]
    )
    publications = models.TextField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_profile'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        default='default.jpg'
    )
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Formation(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='formations'
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre


class Course(models.Model):
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    titre = models.CharField(max_length=200)
    td_file = models.FileField(
        upload_to='courses/td/',
        null=True, blank=True,
        validators=[FileExtensionValidator(['pdf'])]
    )
    tp_file = models.FileField(
        upload_to='courses/tp/',
        null=True, blank=True,
        validators=[FileExtensionValidator(['pdf'])]
    )
    correction = models.FileField(
        upload_to='courses/corrections/',
        null=True, blank=True,
        validators=[FileExtensionValidator(['pdf'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre} ({self.formation.titre})"


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.get_full_name()} enrolled in {self.formation.titre}"
class AssignmentSubmission(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assignment_submissions'  # changed from 'submissions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignment_submissions'  # changed from 'submissions'
    )
    file = models.FileField(
        upload_to='assignments/',
        validators=[FileExtensionValidator(['pdf'])],
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.titre}"
