
from django.contrib import admin
from django.contrib.auth.models import User
from .models import Patient, Department, Doctor, Appointment
from .forms import DoctorCreationForm, DoctorUpdateForm
from .models import Patient, Department, Doctor, Appointment, PatientVisit


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'get_full_name',
        'user',
        'phone_number',
        'date_of_birth',
        'created_at',
    )

    list_display_links = ('get_full_name',)

    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'phone_number',
    )

    list_filter = ('created_at',)

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    get_full_name.short_description = 'Full Name'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    add_form = DoctorCreationForm

    list_display = (
        'id',
        'user',
        'department',
        'phone_number',
        'consultation_fee'
    )
    list_display_links = ('user',)

    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    )

    list_filter = ('department',)

    def get_form(self, request, obj=None, **kwargs):

        if obj is None:
            kwargs['form'] = self.add_form
        else:
            kwargs['form'] = DoctorUpdateForm

        return super().get_form(request, obj, **kwargs)


    def get_fields(self, request, obj=None):

        if obj is None:
            return [
                'first_name',
                'last_name',
                'email',
                'username',
                'password1',
                'password2',
                'department',
                'phone_number',
                'qualification',
                'consultation_fee',
            ]

        return super().get_fields(request, obj)

    def save_model(self, request, obj, form, change):

        if not change and not obj.user_id:

            user = User(
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
            )

            user.set_password(
                form.cleaned_data['password1']
            )

            user.save()
            obj.user = user

        elif change:

            obj.user.first_name = form.cleaned_data['first_name']
            obj.user.last_name = form.cleaned_data['last_name']
            obj.user.email = form.cleaned_data['email']

            obj.user.save()

        super().save_model(request, obj, form, change)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'patient',
        'doctor',
        'appointment_date',
        'status',
        'created_at'
    )

    search_fields = (
        'patient__user__username',
        'doctor__user__username',
    )

    list_filter = (
        'status',
        'appointment_date',
        'doctor__department',
    )

    list_editable = ('status',)

    ordering = ('-appointment_date',)

@admin.register(PatientVisit)
class PatientVisitAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'patient',
        'doctor',
        'visit_type',
        'status',
        'visit_date',
        'created_by',
    )

    list_filter = ('visit_type', 'status', 'visit_date')

    search_fields = (
        'patient__user__first_name',
        'patient__user__last_name',
        'doctor__user__first_name',
        'doctor__user__last_name',
    )