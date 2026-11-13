
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Patient, Doctor


class PatientRegistrationForm(UserCreationForm):

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)

    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3})
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'date_of_birth',
            'address',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            Patient.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                address=self.cleaned_data['address']
            )

        return user


class PatientProfileForm(forms.ModelForm):

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = Patient
        fields = [
            'phone_number',
            'date_of_birth',
            'address',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'address': forms.Textarea(
                attrs={'rows': 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = (
                self.instance.user.first_name
            )
            self.fields['last_name'].initial = (
                self.instance.user.last_name
            )
            self.fields['email'].initial = (
                self.instance.user.email
            )

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })

    def save(self, commit=True):
        patient = super().save(commit=False)

        patient.user.first_name = self.cleaned_data['first_name']
        patient.user.last_name = self.cleaned_data['last_name']
        patient.user.email = self.cleaned_data['email']

        if commit:
            patient.user.save()
            patient.save()

        return patient


class DoctorCreationForm(forms.ModelForm):

    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )

    class Meta:
       model = Doctor
       fields = [
        'department',
        'phone_number',
        'qualification',
        'consultation_fee',
    ]

    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)

       self.order_fields([
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
    ])

    def clean_username(self):
        username = self.cleaned_data['username']

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2:
            if password1 != password2:
                self.add_error(
                    'password2',
                    "The passwords do not match."
                )
            else:
                try:
                    validate_password(password1)
                except forms.ValidationError as error:
                    self.add_error('password1', error)

        return cleaned_data

    def save(self, commit=True):
        doctor = super().save(commit=False)

        user = User(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email'],
        )

        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
            doctor.user = user
            doctor.save()

        return doctor


class DoctorUpdateForm(forms.ModelForm):

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = Doctor
        fields = [
            'first_name',
            'last_name',
            'email',
            'department',
            'phone_number',
            'qualification',
            'consultation_fee',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = (
                self.instance.user.first_name
            )
            self.fields['last_name'].initial = (
                self.instance.user.last_name
            )
            self.fields['email'].initial = (
                self.instance.user.email
            )

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exclude(
            pk=self.instance.user.pk
        ).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    def save(self, commit=True):
        doctor = super().save(commit=False)

        doctor.user.first_name = self.cleaned_data['first_name']
        doctor.user.last_name = self.cleaned_data['last_name']
        doctor.user.email = self.cleaned_data['email']

        if commit:
            doctor.user.save()
            doctor.save()

        return doctor


class ReceptionistPatientRegistrationForm(forms.ModelForm):

    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)

    class Meta:
        model = Patient
        fields = [
            'phone_number',
            'date_of_birth',
            'address',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'address': forms.Textarea(
                attrs={'rows': 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.order_fields([
            'first_name',
            'last_name',
            'username',
            'email',
            'phone_number',
            'date_of_birth',
            'address',
        ])

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data['username']

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    def save(self, commit=True):
        patient = super().save(commit=False)

        user = User(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data.get('email', ''),
        )

        user.set_unusable_password()

        if commit:
            user.save()
            patient.user = user
            patient.save()

        return patient
