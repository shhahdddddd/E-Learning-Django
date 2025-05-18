
from django.urls import path
from . import views

app_name = 'enseignants'

urlpatterns = [
    path('publier/', views.create_formation, name='publier'),
    path('formations/', views.formations, name='formations'),
    path('formation/create/', views.create_formation, name='create_formation'),
    path('formation/edit/<int:pk>/', views.edit_formation, name='edit_formation'),
    path('formation/delete/<int:pk>/', views.delete_formation, name='delete_formation'),
    path('formation/<int:formation_pk>/course/create/', views.create_course, name='create_course'),
    path('course/edit/<int:pk>/', views.edit_course, name='edit_course'),
    path('course/delete/<int:pk>/', views.delete_course, name='delete_course'),
    path('course/submit/<int:pk>/', views.submit_assignment, name='submit_assignment'),
    path('formation/buy/<int:pk>/', views.buy_formation, name='buy_formation'),
    path('course/<int:course_pk>/submissions/', views.view_submissions, name='view_submissions'),
    path('formation/<int:formation_pk>/students/', views.view_enrolled_students, name='view_enrolled_students'),
    path('teacher/<int:teacher_id>/cv/', views.view_teacher_cv, name='view_teacher_cv'),
]