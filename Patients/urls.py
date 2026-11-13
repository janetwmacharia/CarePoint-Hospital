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
    'receptionist-dashboard/',
    views.receptionist_dashboard,
    name='receptionist_dashboard'
),

    path(
        'patient-details/<int:patient_id>/',
        views.patient_details,
        name='patient_details'
    ),

path(
    'update-patient/<int:patient_id>/<int:visit_id>/',
    views.update_patient,
    name='update_patient'
),

    # Patient List
    path('patients/', views.patient_list, name='patient_list'),

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

path(
    'archive-patient/<int:patient_id>/',
    views.archive_patient,
    name='archive_patient'
),

path(
    'receptionist/patient-search/',
    views.receptionist_patient_search,
    name='receptionist_patient_search'
),

path(
    'receptionist/patient/<int:patient_id>/',
    views.receptionist_patient_details,
    name='receptionist_patient_details'
),

path(
    'receptionist/patient-register/',
    views.receptionist_patient_register,
    name='receptionist_patient_register'
),

]