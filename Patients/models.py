
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='doctors'
    )
    phone_number = models.CharField(max_length=20)
    qualification = models.CharField(max_length=150)
    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"


class Patient(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    address = models.TextField()

     # Patient account activation status
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Appointment(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    appointment_date = models.DateTimeField()

    reason = models.TextField(
        blank=True,
        help_text="Briefly describe the reason for your visit."
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.patient} - {self.doctor} "
            f"({self.appointment_date})"
        )

class MedicalRecord(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_records'
    )

   visit = models.ForeignKey(
    'PatientVisit',
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name='medical_records'
)

doctor = models.ForeignKey(
    Doctor,
    on_delete=models.PROTECT,
    related_name='medical_records'
)
appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_records'
    )

diagnosis = models.TextField()
treatment = models.TextField(blank=True)
prescription = models.TextField(blank=True)
doctors_notes = models.TextField(blank=True)

follow_up_date = models.DateField(
        null=True,
        blank=True
    )

created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)


def clean(self):
        super().clean()

        if self.appointment:
            if self.appointment.patient_id != self.patient_id:
                raise ValidationError({
                    'appointment': 'This appointment does not belong to this patient.'
                })

            if self.appointment.doctor_id != self.doctor_id:
                raise ValidationError({
                    'appointment': 'This appointment is not assigned to this doctor.'
                })

def __str__(self):
        return f"Medical Record - {self.patient} ({self.created_at.date()})"


class PatientVisit(models.Model):

    VISIT_TYPE_CHOICES = [
        ('Booked', 'Booked Appointment'),
        ('Walk-in', 'Walk-in'),
    ]

    STATUS_CHOICES = [
        ('Waiting', 'Waiting'),
        ('In Consultation', 'In Consultation'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='visits'
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name='visits'
    )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visits'
    )

    visit_type = models.CharField(
        max_length=20,
        choices=VISIT_TYPE_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Waiting'
    )

    visit_date = models.DateTimeField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='registered_patient_visits'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.patient} - {self.visit_type} "
            f"({self.visit_date})"
        )
    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.patient.is_active:
            raise ValidationError(
                "Archived patients cannot have new visits."
            )

        if self.visit_type == 'Booked' and not self.appointment:
            raise ValidationError(
                "A booked visit must be linked to an appointment."
            )

        if self.visit_type == 'Walk-in' and self.appointment:
            raise ValidationError(
                "A walk-in visit cannot be linked to an appointment."
            )

        if self.appointment:
            if self.appointment.patient != self.patient:
                raise ValidationError(
                    "The appointment belongs to a different patient."
                )

            if self.appointment.doctor != self.doctor:
                raise ValidationError(
                    "The appointment is assigned to a different doctor."
                )