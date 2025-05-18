from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import FileExtensionValidator



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, is_teacher=False, is_student=False, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            is_teacher=is_teacher,
            is_student=is_student,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    cv = models.FileField(upload_to='cvs/', null=True, blank=True, validators=[FileExtensionValidator(['pdf', 'docx'])])
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def save(self, *args, **kwargs):
        if self.is_teacher:
            self.is_student = False
        elif self.is_student:
            self.is_teacher = False
        super().save(*args, **kwargs)


class Purchase(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    formation = models.ForeignKey(
        'enseignants.Formation',
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ['student', 'formation']

    def __str__(self):
        return f"{self.student.get_full_name()} purchased {self.formation.titre}"

class CourseSubmission(models.Model):
    course = models.ForeignKey(
        'enseignants.Course',  # String-based reference to resolve the circular dependency
        on_delete=models.CASCADE,
        related_name='course_submissions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_submissions'
    )
    file = models.FileField(
        upload_to='assignments/',
        validators=[FileExtensionValidator(['pdf'])],
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.titre}"
