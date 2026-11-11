from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import PatientRegistrationForm, PatientProfileForm
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Appointment, Doctor, Patient
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

            # Other accounts
            elif user.is_superuser:
                return redirect('/admin/')

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

    # Get the logged-in doctor's profile
    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    # Find the patient who has an appointment with this doctor
    patient = get_object_or_404(
        Patient.objects.filter(
            appointments__doctor=doctor
        ).distinct(),
        id=patient_id
    )

    # Get this patient's appointment history with this doctor
    appointments = Appointment.objects.filter(
        patient=patient,
        doctor=doctor
    ).select_related(
        'doctor__user',
        'doctor__department'
    ).order_by('-appointment_date')

    return render(request, 'patient_details.html', {
        'patient': patient,
        'appointments': appointments,
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
    allowed_statuses = ['Confirmed', 'Rejected', 'Completed']

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

    # Only allow confirmed appointments to be completed
    elif appointment.status == 'Confirmed' and new_status == 'Completed':
        appointment.status = new_status
        appointment.save()
        messages.success(
            request,
            'Appointment marked as completed.'
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

def home(request):
    return render(request, 'index.html')

