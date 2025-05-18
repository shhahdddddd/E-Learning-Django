from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.contrib import messages
from django import forms
from enseignants.models import Formation
from .models import Enrollment, Submission
from accounts.models import Purchase  # Add this import
import stripe
from django.conf import settings
from django.urls import reverse
import logging
from enseignants.models import Course

# Set up logging
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class SubmissionForm(forms.Form):
    fichier = forms.FileField(label='Fichier', widget=forms.FileInput(attrs={'accept': '.pdf,.docx', 'class': 'form-control'}))

    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        if fichier:
            if not fichier.name.lower().endswith(('.pdf', '.docx')):
                raise forms.ValidationError("Seuls les fichiers PDF et DOCX sont acceptés.")
            if fichier.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("La taille du fichier ne doit pas dépasser 5 Mo.")
        return fichier

@login_required
def formation_detail(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    
    # Check user permissions
    if not (request.user.is_student or request.user.is_teacher or request.user.is_superuser):
        messages.error(request, "Vous n'avez pas accès à cette formation.")
        return redirect('formations')
    
    # Determine enrollment status for students
    is_enrolled = False
    if request.user.is_student:
        is_enrolled = Enrollment.objects.filter(student=request.user, formation=formation).exists()
    elif request.user.is_teacher or request.user.is_superuser:
        is_enrolled = True
    
    # Log enrollment status for debugging
    logger.debug(f"User: {request.user.email}, Formation: {formation.id}, is_enrolled: {is_enrolled}")
    
    submission_form = SubmissionForm()

    # Check if there are any courses in this formation
    has_courses = formation.courses.exists()

    # For each course, check if the student has already submitted
    submitted_courses = {}
    submitted_course_ids = []
    if is_enrolled and hasattr(request.user, 'is_student') and request.user.is_student:
        for course in formation.courses.all():
            submitted = Submission.objects.filter(course=course, student=request.user).exists()
            submitted_courses[course.id] = submitted
            if submitted:
                submitted_course_ids.append(course.id)

    return render(request, 'formation_detail.html', {
        'formation': formation,
        'is_enrolled': is_enrolled,
        'submission_form': submission_form,
        'submitted_courses': submitted_courses,
        'submitted_course_ids': submitted_course_ids,
        'has_courses': has_courses
    })
@login_required
def buy_formation(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    
    if not request.user.is_student:
        messages.error(request, "Seuls les étudiants peuvent acheter des formations.")
        return redirect('formations')
    
    if Enrollment.objects.filter(student=request.user, formation=formation).exists():
        messages.info(request, "Vous êtes déjà inscrit à cette formation.")
        return redirect('etudiant:formation_detail', pk=formation.id)
    
    # Handle GET request - show the purchase confirmation page
    if request.method != 'POST':
        return render(request, 'buy_formation.html', {
            'formation': formation,
        })
    
    # Handle POST request - process the purchase
    user_identifier = request.user.email or f"User_{request.user.id}"
    logger.debug(f"Formation price for {formation.titre}: {formation.prix} (type: {type(formation.prix)})")
    
    # Handle free formations with explicit zero check
    if formation.prix == 0 or float(formation.prix) == 0.0:
        try:
            # Create enrollment
            enrollment = Enrollment.objects.create(student=request.user, formation=formation)
            logger.info(f"Free enrollment created for user {user_identifier} in formation {formation.titre}")
            
            # Create purchase record for free enrollment
            purchase = Purchase.objects.create(
                student=request.user,
                formation=formation,
                is_paid=True  # Free enrollments are considered paid
            )
            logger.info(f"Purchase record created for free enrollment: user {user_identifier} in formation {formation.titre}")
            
            messages.success(request, "Inscription réussie ! Vous avez maintenant accès à cette formation gratuite.")
            return redirect('etudiant:formation_detail', pk=formation.id)
        except Exception as e:
            logger.error(f"Error creating free enrollment for user {user_identifier} in formation {formation.titre}: {str(e)}")
            messages.error(request, f"Erreur lors de l'inscription : {str(e)}")
            return redirect('formations')
    
    # Stripe payment logic for paid formations
    try:
        unit_amount = int(float(formation.prix) * 100)
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': formation.titre,
                    },
                    'unit_amount': unit_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(
                reverse('etudiant:payment_success') + f'?formation_id={formation.id}'
            ),
            cancel_url=request.build_absolute_uri(reverse('etudiant:payment_cancel')),
            metadata={
                'formation_id': str(formation.id),
                'user_id': str(request.user.id)
            }
        )
        logger.info(f"Stripe session created for user {user_identifier} for formation {formation.titre}")
        return redirect(session.url, code=303)
    except Exception as e:
        logger.error(f"Error creating Stripe session for user {user_identifier} in formation {formation.titre}: {str(e)}")
        messages.error(request, f"Erreur lors de la création de la session de paiement : {str(e)}")
        return redirect('formations')
@login_required
def payment_success(request):
    formation_id = request.GET.get('formation_id')
    user_identifier = request.user.email or f"User_{request.user.id}"
    
    if formation_id:
        try:
            formation = get_object_or_404(Formation, id=formation_id)
            
            # Create or get enrollment
            enrollment, created = Enrollment.objects.get_or_create(
                student=request.user, 
                formation=formation
            )
            logger.info(f"Enrollment {'created' if created else 'retrieved'} for user {user_identifier} in formation {formation.titre}")
            
            # Create purchase record
            purchase, purchase_created = Purchase.objects.get_or_create(
                student=request.user,
                formation=formation,
                defaults={'is_paid': True}
            )
            
            # If purchase already existed but wasn't marked as paid, update it
            if not purchase_created and not purchase.is_paid:
                purchase.is_paid = True
                purchase.save()
                logger.info(f"Updated purchase record for user {user_identifier} in formation {formation.titre}")
            
            messages.success(request, "Paiement réussi ! Vous êtes maintenant inscrit à cette formation.")
            return redirect('etudiant:formation_detail', pk=formation.id)
            
        except Exception as e:
            logger.error(f"Error during payment success for user {user_identifier}, formation_id {formation_id}: {str(e)}")
            messages.error(request, f"Erreur lors de l'inscription : {str(e)}")
    else:
        logger.error(f"Payment success called without formation_id for user {user_identifier}")
        messages.error(request, "Erreur lors du traitement du paiement.")
    return redirect('formations')

@login_required
def payment_cancel(request):
    user_identifier = request.user.email or f"User_{request.user.id}"
    logger.info(f"Payment cancelled for user {user_identifier}")
    messages.warning(request, "Paiement annulé. Vous n'avez pas été inscrit à la formation.")
    return redirect('formations')

@login_required
def submit_assignment(request, pk=None, course_pk=None):
    # Support both URLs: by formation or by course
    if course_pk is not None:
        course = get_object_or_404(Course, pk=course_pk)
        formation = course.formation
    else:
        formation = get_object_or_404(Formation, pk=pk)
        course = None
    
    # Check if the user is a student and enrolled
    if not hasattr(request.user, 'is_student') or not request.user.is_student:
        messages.error(request, "Seuls les étudiants peuvent soumettre des devoirs.")
        return redirect('formations')
    if not Enrollment.objects.filter(student=request.user, formation=formation).exists():
        messages.error(request, "Vous devez être inscrit pour soumettre un devoir.")
        return redirect('etudiant:buy_formation', pk=formation.id)
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            # If course is None (old URL), try to get first course (for backward compatibility)
            if course is None:
                course = formation.courses.first()
                if not course:
                    messages.error(request, "Aucun cours n'est disponible pour cette formation.")
                    return redirect('etudiant:formation_detail', pk=formation.id)
            Submission.objects.create(
                course=course,
                student=request.user,
                file=form.cleaned_data['fichier']
            )
            messages.success(request, f"Devoir soumis avec succès pour le cours : {course.titre}.")
            return redirect('etudiant:formation_detail', pk=formation.id)
        else:
            # Re-render the page with form errors and preserved data
            return render(request, 'formation_detail.html', {
                'formation': formation,
                'is_enrolled': True,
                'submission_form': form
            })
    else:
        # For GET requests, display the empty form
        form = SubmissionForm()
        return render(request, 'formation_detail.html', {
            'formation': formation,
            'is_enrolled': True,
            'submission_form': form
        })