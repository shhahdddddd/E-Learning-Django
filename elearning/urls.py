from django.contrib import admin
from django.urls import path, include
from accounts.views import home ,register # Import your home view
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from .views import carriers,formations
from django.urls import reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import test_reset_confirm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # Root URL
    path('register/', register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('carriers/',carriers, name='carriers'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')),
    path('contact/', views.contact, name='contact'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('home')), name='logout'),
    path('enseignants/',include('enseignants.urls')),
    path('etudiant/',include('etudiant.urls')),
    path('formations/',formations, name='formations'),
    path('test-reset-confirm/', test_reset_confirm, name='test_reset_confirm'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)