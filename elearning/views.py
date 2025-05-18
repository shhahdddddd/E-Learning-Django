from django.shortcuts import render,redirect
from enseignants.models import Formation,UserProfile
from enseignants.forms import ProfilePictureForm
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings


def test_reset_confirm(request):
    return render(request, 'registration/password_reset_confirm.html', {'validlink': True})
def carriers(request):
    formations = Formation.objects.all()
    return render(request, 'carriers.html', {'formations': formations})
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def formations(request):
    if hasattr(request.user, 'is_teacher') and request.user.is_teacher and not request.user.is_superuser:
        # Redirect teachers to the enseignants formations view
        return redirect('enseignants:formations')
    formations = Formation.objects.all()
    return render(request, 'formations.html', {'formations': formations})
@login_required
def profile_view(request):
    # Get or create the user's profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfilePictureForm(instance=user_profile)

    context = {
        'user': request.user,
        'profile': user_profile,  # Keep the context key as 'profile' for consistency
        'form': form,
    }
    return render(request, 'profile.html', context)

def contact(request):
    """View to handle contact form display and submission."""
    if request.method == 'POST':
        # Form was submitted
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject', '')
        message = request.POST.get('message', '')
        consent = request.POST.get('consent', False)
        
        # Basic validation
        if name and email and subject and message and consent:
            # Prepare email content
            email_subject = f"Contact Form: {subject}"
            email_message = f"""
            Nouveau message depuis le formulaire de contact:
            
            Nom: {name}
            Email: {email}
            Téléphone: {phone}
            Sujet: {subject}
            
            Message:
            {message}
            """
            
            try:
                # Send email to admin
                send_mail(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,  # From email (set in settings.py)
                    [settings.CONTACT_EMAIL],  # To email (set in settings.py)
                    fail_silently=False,
                )
                
                # Success message
                messages.success(request, "Votre message a été envoyé avec succès. Nous vous répondrons dans les plus brefs délais.")
                return redirect('contact')
            except Exception as e:
                # Error message
                messages.error(request, "Une erreur s'est produite lors de l'envoi du message. Veuillez réessayer plus tard.")
        else:
            # Invalid form submission
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
    
    # Display the contact form (GET request or form submission failed)
    return render(request, 'contact.html')