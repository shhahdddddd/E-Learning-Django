from django.urls import path
from . import views

app_name = 'etudiant'   # <<< this is IMPORTANT!

urlpatterns = [
    path('buy/<int:pk>/', views.buy_formation, name='buy_formation'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('formation/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    path('course/<int:course_pk>/submit/', views.submit_assignment, name='submit_course_assignment'),
    path('formation/<int:pk>/buy/', views.formation_detail, name='formation_detail'),
    
]


