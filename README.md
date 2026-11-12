
# CarePoint Hospital Management System

## Project Overview

CarePoint Hospital is a web-based hospital management system developed using Django. It is designed to support basic hospital operations by connecting patients, doctors and administrators through one platform.

The system allows patients to register, book appointments and manage their profiles, while doctors can manage appointments and access patient information.

## User Roles

- **Administrator:** Manages patients, doctors, departments and appointments.
- **Doctor:** Views assigned appointments, updates appointment statuses and accesses patient details.
- **Patient:** Registers, books appointments, views appointment history and manages their profile.

## Key Features

- Patient registration and authentication.
- Doctor registration and authentication.
- Appointment booking and management.
- Doctor dashboard and appointment filters.
- Patient and doctor profile management.
- Patient details and appointment history.
- Administrator management of doctors, patients and departments.
- Administrator-controlled patient deletion.

## Technologies Used

- Python
- Django
- SQLite
- HTML5
- CSS3
- Bootstrap 5
- Bootstrap Icons
- Git and GitHub

## Patient Record Management

The system supports CRUD operations:

- **Create:** Register patient accounts.
- **Read:** View patient information and appointment history.
- **Update:** Edit patient profile information.
- **Delete:** Administrators can delete patient records through Django Administration.

Deleting a patient also removes their linked user account and associated appointments through Django's cascading deletion behaviour.

## Installation and Setup

1. Clone the repository:

   `git clone https://github.com/janetwmacharia/CarePoint-Hospital.git`

2. Navigate to the project directory:

   `cd CarePoint-Hospital`

3. Create and activate a virtual environment.

4. Install Django:

   `pip install django`

5. Apply database migrations:

   `py manage.py migrate`

6. Create an administrator account:

   `py manage.py createsuperuser`

7. Start the development server:

   `py manage.py runserver`

8. Open `http://127.0.0.1:8000/` in your browser.

## Project Status

The core hospital management features have been implemented. Frontend improvements and additional functionality are ongoing.

## Developer

Business Information Technology student interested in developing practical technology solutions for business and organisational needs.
