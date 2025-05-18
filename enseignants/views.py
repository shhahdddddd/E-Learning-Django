from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import Http404, FileResponse
from django.conf import settings
import os
from .forms import FormationForm, CourseForm
from .models import Formation, Course, AssignmentSubmission, EnseignantProfile
from etudiant.models import Submission  # Student submissions
from accounts.models import Purchase, User
import logging
logger = logging.getLogger(__name__)

@login_required
def create_formation(request):
    """View for publishing new formations (combines with create_formation)"""
    if not request.user.is_teacher:
        return redirect('enseignants:formations')
    
    if request.method == 'POST':
        form = FormationForm(request.POST, request.FILES)
        if form.is_valid():
            formation = form.save(commit=False)
            formation.teacher = request.user
            formation.save()
            messages.success(request, "Formation créée avec succès!")
            return redirect('enseignants:formations')
    else:
        form = FormationForm()
    
    return render(request, 'publier.html', {'form': form})

@login_required
def formations(request):
    """List all formations with purchase status"""
    print(f"[DEBUG] Logged-in teacher: {getattr(request.user, 'username', getattr(request.user, 'email', str(request.user)))}")
    if request.user.is_teacher and not request.user.is_superuser:
        formations = Formation.objects.filter(teacher=request.user)
    else:
        formations = Formation.objects.all()
    print(f"[DEBUG] Found {formations.count()} formations for this teacher.")
    purchased_formations = Purchase.objects.filter(
        student=request.user
    ).values_list('formation_id', flat=True)
    from .models import AssignmentSubmission  # Only import AssignmentSubmission here
    for formation in formations:
        print(f"[DEBUG] Formation: {formation.titre} (ID={formation.id})")
        for course in formation.courses.all():
            print(f"    [DEBUG] Course: {course.titre} (ID={course.id})")
            student_submissions = list(Submission.objects.filter(course=course))
            assignment_submissions = list(AssignmentSubmission.objects.filter(course=course))
            submissions = student_submissions + assignment_submissions
            print(f"        [DEBUG] {len(student_submissions)} student submissions, {len(assignment_submissions)} assignment submissions, {len(submissions)} total.")
            for s in student_submissions:
                print(f"            [DEBUG] Submission: id={s.id}, student={getattr(s.student, 'username', getattr(s.student, 'email', s.student))}, file={s.file}, submitted_at={getattr(s, 'submitted_at', None)}")
            for a in assignment_submissions:
                print(f"            [DEBUG] AssignmentSubmission: id={a.id}, student={getattr(a.student, 'username', getattr(a.student, 'email', a.student))}, file={a.file}, submitted_at={getattr(a, 'submitted_at', None)}")
            course.submissions_for_teacher = submissions
    return render(request, 'formations.html', {
        'formations': formations,
        'purchased_formations': purchased_formations,
    })

@login_required
def delete_formation(request, pk):
    """Delete a formation"""
    formation = get_object_or_404(Formation, pk=pk)
    if request.user == formation.teacher or request.user.is_superuser:
        formation.delete()
        messages.success(request, "Formation supprimée avec succès")
    return redirect('enseignants:formations')

@login_required
def edit_formation(request, pk):
    """Edit existing formation"""
    formation = get_object_or_404(Formation, pk=pk)
    if request.user != formation.teacher and not request.user.is_superuser:
        return redirect('enseignants:formations')
    
    if request.method == 'POST':
        form = FormationForm(request.POST, instance=formation)
        if form.is_valid():
            form.save()
            messages.success(request, "Formation mise à jour avec succès")
            return redirect('enseignants:formations')
    else:
        form = FormationForm(instance=formation)
    
    return render(request, 'edit_formation.html', {
        'form': form,
        'formation': formation
    })

@login_required
def create_course(request, formation_pk):
    """Create new course within a formation"""
    formation = get_object_or_404(Formation, pk=formation_pk)
    if request.user != formation.teacher and not request.user.is_superuser:
        return redirect('enseignants:formations')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.formation = formation
            course.save()
            messages.success(request, "Cours créé avec succès")
            return redirect('enseignants:formations')
    else:
        form = CourseForm()
    
    return render(request, 'create_course.html', {
        'form': form,
        'formation': formation
    })

@login_required
def edit_course(request, pk):
    """Edit existing course"""
    course = get_object_or_404(Course, pk=pk)
    if request.user != course.formation.teacher and not request.user.is_superuser:
        return redirect('enseignants:formations')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Cours mis à jour avec succès")
            return redirect('enseignants:formations')
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'edit_course.html', {
        'form': form,
        'course': course
    })

@login_required
def delete_course(request, pk):
    """Delete a course"""
    course = get_object_or_404(Course, pk=pk)
    if request.user == course.formation.teacher or request.user.is_superuser:
        course.delete()
        messages.success(request, "Cours supprimé avec succès")
    return redirect('enseignants:formations')

@login_required
def submit_assignment(request, pk):
    """Submit assignment for a course"""
    course = get_object_or_404(Course, pk=pk)
    
    # Check purchase status
    if not Purchase.objects.filter(
        student=request.user,
        formation=course.formation
    ).exists() and not request.user.is_teacher:
        messages.error(request, "Achat de la formation requis")
        return redirect('enseignants:formations')
    
    if request.method == 'POST' and 'file' in request.FILES:
        AssignmentSubmission.objects.create(
            course=course,
            student=request.user,
            file=request.FILES['file']
        )
        messages.success(request, "Travail soumis avec succès")
        return redirect('enseignants:formations')
    
    return render(request, 'submit_assignment.html', {'course': course})

@login_required
def buy_formation(request, pk):
    """Purchase a formation"""
    formation = get_object_or_404(Formation, pk=pk)
    
    if request.user.is_teacher:
        messages.error(request, "Enseignants ne peuvent pas acheter")
        return redirect('enseignants:formations')
    
    if request.method == 'POST':
        Purchase.objects.create(formation=formation, student=request.user)
        messages.success(request, "Formation achetée avec succès")
        return redirect('enseignants:formations')
    
    return render(request, 'buy_formation.html', {'formation': formation})

import logging
from django.db.models import Q
from accounts.models import Purchase

logger = logging.getLogger(__name__)

@login_required
def view_enrolled_students(request, formation_pk):
    """View to display all students enrolled in a formation"""
    try:
        formation = get_object_or_404(Formation, pk=formation_pk)
        
        # Check if the current user is the teacher of this formation
        if request.user != formation.teacher and not request.user.is_superuser:
            messages.error(request, "Vous n'êtes pas autorisé à voir les étudiants de cette formation.")
            return redirect('enseignants:formations')
        
        # Debug: Print formation details
        print("\n" + "="*50)
        print(f"[DEBUG] Viewing enrolled students for formation: {formation.titre} (ID: {formation.id})")
        print(f"[DEBUG] Teacher: {formation.teacher}")
        
        # Get all purchases for this formation
        purchases = Purchase.objects.filter(
            formation=formation
        ).select_related('student')
        
        # Debug: Print all purchases
        print(f"[DEBUG] Found {purchases.count()} purchases for this formation")
        for p in purchases:
            print(f"[DEBUG] - Purchase ID: {p.id}, Student: {p.student.email if p.student else 'None'}, "
                  f"Paid: {p.is_paid}, Date: {p.purchased_at}")
        
        # Get unique students (in case of multiple purchases)
        students = {}
        for purchase in purchases:
            if purchase.student and purchase.student.id not in students:
                students[purchase.student.id] = {
                    'student': purchase.student,
                    'purchased_at': purchase.purchased_at,
                    'is_paid': purchase.is_paid
                }
        
        # Debug: Print unique students
        print(f"[DEBUG] Found {len(students)} unique students")
        for student_id, data in students.items():
            print(f"[DEBUG] - Student: {data['student'].email}, "
                  f"Paid: {data['is_paid']}, Date: {data['purchased_at']}")
        print("="*50 + "\n")
        
        # Convert to list for template
        students_list = list(students.values())
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error in view_enrolled_students: {str(e)}")
        print(traceback.format_exc())
        students_list = []
        messages.error(request, f"Une erreur est survenue : {str(e)}")
    
    return render(request, 'enrolled_students.html', {
        'formation': formation,
        'students': students_list,
        'total_students': len(students_list)
    })

@login_required
def view_teacher_cv(request, teacher_id):
    """View to display teacher's CV"""
    try:
        teacher = User.objects.get(id=teacher_id, is_teacher=True)
        enseignant_profile = get_object_or_404(EnseignantProfile, user=teacher)
        
        if not enseignant_profile.cv:
            raise Http404("CV not found")
            
        # Get the file path
        file_path = os.path.join(settings.MEDIA_ROOT, str(enseignant_profile.cv))
        
        # Open the file and serve it as a response
        try:
            response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
            return response
        except FileNotFoundError:
            raise Http404("CV file not found")
            
    except User.DoesNotExist:
        raise Http404("Teacher not found")

@login_required
def view_submissions(request, course_pk):
    """View all submissions for a course"""
    course = get_object_or_404(Course, pk=course_pk)
    logger.debug(f"[Teacher View] Viewing submissions for course id={course.id}, title={course.titre}")
    logger.debug(f"[Teacher View] Logged-in teacher: {request.user} | Course owner: {course.formation.teacher}")

    # Check if user is the course teacher or superuser
    if request.user != course.formation.teacher and not request.user.is_superuser:
        messages.error(request, f"Vous n'êtes pas autorisé à voir les soumissions de ce cours. Seul l'enseignant créateur ({course.formation.teacher}) peut voir les soumissions.")
        return redirect('enseignants:formations')

    # Get all submissions from both models
    student_submissions = Submission.objects.filter(course=course).select_related('student')
    assignment_submissions = AssignmentSubmission.objects.filter(course=course).select_related('student')
    
    # Combine submissions from both models
    all_submissions = list(student_submissions) + list(assignment_submissions)
    
    # Process each submission to ensure they have the required attributes
    for sub in all_submissions:
        # Ensure student has get_full_name method
        if hasattr(sub, 'student') and not hasattr(sub.student, 'get_full_name'):
            sub.student.get_full_name = lambda: getattr(sub.student, 'name', '') or getattr(sub.student, 'email', 'Étudiant inconnu')
            
        # Ensure submitted_at is set
        if not hasattr(sub, 'submitted_at'):
            sub.submitted_at = getattr(sub, 'created_at', timezone.now())
        
        # Ensure file attribute is set (some might use 'fichier' instead)
        if not hasattr(sub, 'file'):
            sub.file = getattr(sub, 'fichier', None)
    
    # Sort by submission date (newest first)
    all_submissions.sort(key=lambda x: x.submitted_at if hasattr(x, 'submitted_at') and x.submitted_at else timezone.now(), reverse=True)
    
    # Log the number of submissions found for debugging
    logger.debug(f"[Teacher View] Found {len(all_submissions)} submissions for course {course.id}")
    for sub in all_submissions:
        logger.debug(f"[Teacher View] Submission: {sub.id} by {getattr(sub.student, 'email', 'Unknown')} at {getattr(sub, 'submitted_at', 'No date')}")
    
    return render(request, 'view_submissions.html', {
        'course': course,
        'submissions': all_submissions,
        'submission_count': len(all_submissions)
    })