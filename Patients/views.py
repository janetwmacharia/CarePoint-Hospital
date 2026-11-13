from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import PatientRegistrationForm, PatientProfileForm, ReceptionistPatientRegistrationForm
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Appointment, Doctor, Patient, MedicalRecord, PatientVisit
from django.db.models import Q
from django.views.decorators.http import require_POST

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')

    else:
        form = PatientRegistrationForm()

    return render(request, 'register.html', {'form': form})

def userlogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # Check whether the user is a doctor
            if hasattr(user, 'doctor_profile'):
                return redirect('doctor_dashboard')

            # Check whether the user is a patient
            elif hasattr(user, 'patient_profile'):
                return redirect('dashboard')

                       # Administrator
            elif user.is_superuser:
                return redirect('/admin/')

            # Receptionist
            elif user.groups.filter(name='Receptionists').exists():
                return redirect('receptionist_dashboard')

            # Accounts without an assigned role
            else:
                logout(request)
                return render(request, 'login.html', {
                    'error': 'Your account does not have an assigned role.'
                })

        else:
            return render(request, 'login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'login.html')

@login_required
def booking(request):

    doctors = Doctor.objects.select_related(
        'user', 'department'
    ).all()

    if request.method == 'POST':

        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        reason = request.POST.get('reason', '')

        try:
            patient = request.user.patient_profile
            doctor = Doctor.objects.get(id=doctor_id)

            appointment_datetime = datetime.fromisoformat(
                appointment_date
            )

            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(
                    appointment_datetime
                )

            if appointment_datetime <= timezone.now():
                raise ValueError(
                    "Please select a future appointment date and time."
                )

            Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_datetime,
                reason=reason,
                status='Pending'
            )

            messages.success(
                request,
                'Your appointment request has been submitted successfully!'
            )

            return redirect('dashboard')

        except Patient.DoesNotExist:
            messages.error(
                request,
                'Please complete your patient profile before booking.'
            )

        except (Doctor.DoesNotExist, ValueError, TypeError):
            messages.error(
                request,
                'Please select a valid doctor and appointment date.'
            )

          # ADD THE RENDER STATEMENT HERE, AT THE BOTTOM
    return render(request, 'booking.html', {
        'doctors': doctors,
        'min_datetime': timezone.localtime().strftime(
            '%Y-%m-%dT%H:%M'
        )
    })

def patient_list(request):
    patients = Patient.objects.all().order_by('id')

    return render(request, 'patient_list.html', {
        'patients': patients
    })

@login_required
def dashboard(request):

    appointments = Appointment.objects.filter(
        patient__user=request.user
    ).select_related(
        'doctor__user',
        'doctor__department'
    ).order_by('-appointment_date')

    total_appointments = appointments.count()

    pending_appointments = appointments.filter(
        status='Pending'
    ).count()

    available_doctors = Doctor.objects.count()

    return render(request, 'dashboard.html', {
        'user': request.user,
        'appointments': appointments,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'available_doctors': available_doctors,
    })


@login_required
def doctor_dashboard(request):

    # Get the doctor profile linked to the logged-in user
    doctor = Doctor.objects.filter(
        user=request.user
    ).select_related('department', 'user').first()

    # Ensure this account belongs to a doctor
    if not doctor:
        messages.error(
            request,
            'You do not have an assigned doctor profile.'
        )
        return redirect('dashboard')

    # Retrieve all appointments assigned to this doctor
    all_appointments = Appointment.objects.filter(
        doctor=doctor
    ).select_related(
        'patient__user'
    ).order_by('-appointment_date')

        # Retrieve patients who have checked in and are awaiting consultation
    # or are already undergoing consultation
    waiting_visits = PatientVisit.objects.filter(
        doctor=doctor,
        patient__is_active=True,
        status__in=['Waiting', 'In Consultation']
    ).select_related(
        'patient__user',
        'appointment'
    ).order_by('visit_date')

    # Calculate dashboard statistics using all appointments
    total_appointments = all_appointments.count()

    pending_appointments = all_appointments.filter(
        status='Pending'
    ).count()

    confirmed_appointments = all_appointments.filter(
        status='Confirmed'
    ).count()

    completed_appointments = all_appointments.filter(
        status='Completed'
    ).count()

    total_patients = all_appointments.values(
        'patient'
    ).distinct().count()

    # Available appointment status filters
    status_choices = [
        'Pending',
        'Confirmed',
        'Rejected',
        'Cancelled',
        'Completed'
    ]

    # Get the selected filter from the URL
    status_filter = request.GET.get('status', 'All')

    # Apply the selected filter
    if status_filter in status_choices:
        appointments = all_appointments.filter(
            status=status_filter
        )
    else:
        status_filter = 'All'
        appointments = all_appointments

    return render(request, 'doctor_dashboard.html', {
        'doctor': doctor,
        'appointments': appointments,
        'waiting_visits': waiting_visits,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'completed_appointments': completed_appointments,
        'total_patients': total_patients,
        'status_filter': status_filter,
        'status_choices': status_choices,
    })

@login_required
def patient_details(request, patient_id):

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    # Allow access where the doctor has an appointment
    # or an assigned patient visit
    patient = get_object_or_404(
        Patient.objects.filter(
            Q(appointments__doctor=doctor) |
            Q(visits__doctor=doctor)
        ).distinct(),
        id=patient_id
    )

    appointments = Appointment.objects.filter(
        patient=patient,
        doctor=doctor
    ).select_related(
        'doctor__user',
        'doctor__department'
    ).order_by('-appointment_date')

    # Retrieve visits assigned to this doctor
    visits = PatientVisit.objects.filter(
        patient=patient,
        doctor=doctor
    ).select_related(
        'appointment'
    ).order_by('-visit_date')

    medical_records = MedicalRecord.objects.filter(
        patient=patient
    ).select_related(
        'doctor__user',
        'visit'
    ).order_by('-created_at')

    return render(request, 'patient_details.html', {
        'patient': patient,
        'appointments': appointments,
        'visits': visits,
        'medical_records': medical_records,
    })

@login_required
@require_POST
def archive_patient(request, patient_id):

    # Confirm that the logged-in user is a doctor
    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    # Only allow doctors to archive patients
    # who have appointments with them
    patient = get_object_or_404(
        Patient.objects.filter(
            appointments__doctor=doctor
        ).distinct(),
        id=patient_id
    )

    if not patient.is_active:
        messages.info(request, 'This patient is already archived.')
        return redirect(
            'patient_details',
            patient_id=patient.id
        )

    # Deactivate the patient without deleting records
    patient.is_active = False
    patient.save(update_fields=['is_active'])

    messages.success(
        request,
        'Patient successfully archived. Medical history has been preserved.'
    )

    return redirect('doctor_dashboard')


@login_required
def update_patient(request, patient_id, visit_id):

    # Get the logged-in doctor's profile
    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    # Get the specific visit assigned to this doctor and patient
    visit = get_object_or_404(
        PatientVisit.objects.select_related(
            'patient__user',
            'doctor__user',
            'appointment'
        ),
        id=visit_id,
        patient_id=patient_id,
        doctor=doctor
    )

    patient = visit.patient

    # Prevent consultations for archived patients
    if not patient.is_active:
        messages.error(
            request,
            'This patient is archived and cannot receive a new consultation.'
        )
        return redirect('doctor_dashboard')

    # Only allow consultations for visits awaiting or undergoing consultation
    if visit.status not in ['Waiting', 'In Consultation']:
        messages.error(
            request,
            'This visit is no longer available for consultation.'
        )
        return redirect('doctor_dashboard')

        # Mark the visit as in consultation when the doctor opens it
    if visit.status == 'Waiting':
        visit.status = 'In Consultation'
        visit.save(update_fields=['status'])

    # Prevent more than one medical record for the same visit
    if MedicalRecord.objects.filter(visit=visit).exists():
        messages.error(
            request,
            'A medical record already exists for this visit.'
        )
        return redirect(
            'patient_details',
            patient_id=patient.id
        )

    if request.method == 'POST':

        diagnosis = request.POST.get('diagnosis', '').strip()
        treatment = request.POST.get('treatment', '').strip()
        prescription = request.POST.get('prescription', '').strip()
        doctors_notes = request.POST.get('doctors_notes', '').strip()
        follow_up_date = request.POST.get('follow_up_date') or None

        if not diagnosis:
            messages.error(request, 'Diagnosis is required.')

        else:
            try:
                if follow_up_date:
                    follow_up_date = datetime.strptime(
                        follow_up_date, '%Y-%m-%d'
                    ).date()

                from django.db import transaction

                with transaction.atomic():

                    # Create the medical record linked to this visit
                    MedicalRecord.objects.create(
                        patient=patient,
                        doctor=doctor,
                        visit=visit,
                        appointment=visit.appointment,
                        diagnosis=diagnosis,
                        treatment=treatment,
                        prescription=prescription,
                        doctors_notes=doctors_notes,
                        follow_up_date=follow_up_date
                    )

                    # Complete the visit after the consultation is saved
                    visit.status = 'Completed'
                    visit.save(update_fields=['status'])

                    # Complete the appointment if this was a booked visit
                    if visit.appointment:
                        visit.appointment.status = 'Completed'
                        visit.appointment.save(update_fields=['status'])

                messages.success(
                    request,
                    'Medical record saved and consultation completed successfully!'
                )

                return redirect(
                    'patient_details',
                    patient_id=patient.id
                )

            except ValueError:
                messages.error(
                    request,
                    'Please enter a valid follow-up date.'
                )

    return render(request, 'update_patient.html', {
        'patient': patient,
        'visit': visit,
        'record': None,
    })

@login_required
def doctor_profile(request):

    # Get the logged-in doctor's profile
    doctor = get_object_or_404(
        Doctor.objects.select_related(
            'user',
            'department'
        ),
        user=request.user
    )

    return render(request, 'doctor_profile.html', {
        'doctor': doctor,
    })

@login_required
def profile(request):

    patient = Patient.objects.filter(
        user=request.user
    ).first()

    if not patient:
        messages.error(
            request,
            'Patient profile not found. Please contact the hospital.'
        )
        return redirect('dashboard')

    if request.method == 'POST':
        form = PatientProfileForm(
            request.POST,
            instance=patient
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Your profile has been updated successfully!'
            )

            return redirect('profile')

    else:
        form = PatientProfileForm(instance=patient)

    return render(request, 'profile.html', {
        'user': request.user,
        'patient': patient,
        'form': form,
    })

@login_required
def userlogout(request):
    logout(request)
    return redirect('login')


@login_required
@require_POST
def manage_appointment(request, appointment_id):

    # Get the logged-in doctor's profile
    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    # Get an appointment belonging to this doctor only
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor
    )

    # Get the requested action
    new_status = request.POST.get('status')

    # Define the allowed status changes
    allowed_statuses = ['Confirmed', 'Rejected']

    if new_status not in allowed_statuses:
        messages.error(request, 'Invalid appointment status.')
        return redirect('doctor_dashboard')

    # Only allow pending appointments to be confirmed or rejected
    if appointment.status == 'Pending' and new_status in ['Confirmed', 'Rejected']:
        appointment.status = new_status
        appointment.save()
        messages.success(
            request,
            f'Appointment successfully {new_status.lower()}.'
        )

    else:
        messages.error(
            request,
            'This appointment cannot be updated to that status.'
        )

    return redirect('doctor_dashboard')

@login_required
@require_POST
def cancel_appointment(request, appointment_id):

    # Find the patient profile linked to the logged-in user
    patient = get_object_or_404(
        Patient,
        user=request.user
    )

    # Find the appointment belonging to this patient only
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=patient
    )

    # Allow cancellation only for Pending or Confirmed appointments
    if appointment.status in ['Pending', 'Confirmed']:

        appointment.status = 'Cancelled'
        appointment.save()

        messages.success(
            request,
            'Your appointment has been cancelled successfully.'
        )

    else:
        messages.error(
            request,
            'This appointment cannot be cancelled.'
        )

    return redirect('dashboard')

@login_required
def receptionist_dashboard(request):

    # Only users in the Receptionists group can access this page
    if not request.user.groups.filter(name='Receptionists').exists():
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('login')

    today = timezone.localdate()

    total_patients = Patient.objects.filter(
        is_active=True
    ).count()

    todays_appointments = Appointment.objects.filter(
        appointment_date__date=today
    ).count()

    waiting_patients = PatientVisit.objects.filter(
        status='Waiting',
        patient__is_active=True
    ).count()

    return render(request, 'receptionist_dashboard.html', {
        'total_patients': total_patients,
        'todays_appointments': todays_appointments,
        'waiting_patients': waiting_patients,
    })

@login_required
def receptionist_patient_search(request):

    # Restrict access to receptionists
    if not request.user.groups.filter(name='Receptionists').exists():
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('login')

    search_query = request.GET.get('q', '').strip()

    patients = Patient.objects.none()

    if search_query:
        patients = Patient.objects.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(user__username__icontains=search_query)
        ).select_related(
            'user'
        ).order_by('user__first_name')

    return render(request, 'receptionist_patient_search.html', {
        'patients': patients,
        'search_query': search_query,
    })

@login_required
def receptionist_patient_details(request, patient_id):

    # Restrict access to receptionists
    if not request.user.groups.filter(name='Receptionists').exists():
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('login')

    patient = get_object_or_404(
        Patient.objects.select_related('user'),
        id=patient_id
    )

    # Retrieve appointment history for reception purposes
    appointments = Appointment.objects.filter(
        patient=patient
    ).select_related(
        'doctor__user',
        'doctor__department'
    ).order_by('-appointment_date')

    # Retrieve visit information without exposing clinical notes
    visits = PatientVisit.objects.filter(
        patient=patient
    ).select_related(
        'doctor__user',
        'doctor__department'
    ).order_by('-visit_date')

    return render(request, 'receptionist_patient_details.html', {
        'patient': patient,
        'appointments': appointments,
        'visits': visits,
    })

@login_required
def receptionist_patient_register(request):

    # Restrict access to receptionists
    if not request.user.groups.filter(name='Receptionists').exists():
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('login')

    if request.method == 'POST':
        form = ReceptionistPatientRegistrationForm(request.POST)

        if form.is_valid():
            from django.db import transaction

            try:
                with transaction.atomic():
                    patient = form.save()

                messages.success(
                    request,
                    'Patient registered successfully!'
                )

                return redirect(
                    'receptionist_patient_details',
                    patient_id=patient.id
                )

            except Exception:
                messages.error(
                    request,
                    'An error occurred while registering the patient.'
                )

    else:
        form = ReceptionistPatientRegistrationForm()

    return render(
        request,
        'receptionist_patient_register.html',
        {'form': form}
    )

def home(request):
    return render(request, 'index.html')

