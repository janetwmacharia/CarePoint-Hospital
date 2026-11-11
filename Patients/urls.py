from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.userlogin, name='login'),
    path('logout/', views.userlogout, name='logout'),
    path('booking/', views.booking, name='booking'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),

    path(
    'patient-details/<int:patient_id>/',
    views.patient_details,
    name='patient_details'
),

    path(
    'manage-appointment/<int:appointment_id>/',
    views.manage_appointment,
    name='manage_appointment'
),

path(
    'cancel-appointment/<int:appointment_id>/',
    views.cancel_appointment,
    name='cancel_appointment'
),

path(
    'doctor-profile/',
    views.doctor_profile,
    name='doctor_profile'
),

]