from django.db import models
from django.conf import settings
from enseignants.models import Formation, Course  # Now import Course too

class EtudiantProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='etudiant_profile'
    )

    def __str__(self):
        return f"Profile for {self.user.get_full_name()} ({self.user.email})"

# Corrected Enrollment with unique related_name
class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='etudiant_enrollments')  # Using AUTH_USER_MODEL
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='etudiant_enrollments', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Enrollment for {self.student.get_full_name()} ({self.student.email}) in {self.formation.titre if self.formation else 'No Formation'}"

class Submission(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_student': True},
        related_name='etudiant_submissions'  # avoid clash
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='etudiant_submissions'  # avoid clash with enseignants
    )
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission by {self.student.get_full_name()} ({self.student.email}) for {self.course.titre}"
