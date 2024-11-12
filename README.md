# Appointment Scheduling System

A Django-based appointment scheduling system that allows users to book appointments, ensuring that the number of appointments does not exceed the capacity of available professionals. The system handles overlapping appointments, variable durations, and cancellations, while maintaining data integrity and preventing overbooking.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Models](#models)
- [Validation Logic](#validation-logic)
- [Contributing](#contributing)
- [License](#license)

## Features

- **User Appointment Booking**: Users can schedule appointments by selecting a date and time.
- **Professional Assignment**: A management team can assign professionals to appointments.
- **Availability Checks**: The system ensures that appointments are only booked if professionals are available.
- **Duration Handling**: Supports appointments with variable durations, including extended durations that may span multiple time slots.
- **Overlapping Appointments Prevention**: Validates and prevents overlapping appointments for both general availability and specific professionals.
- **Cancellation Management**: Cancelled appointments are excluded from availability checks, freeing up time slots for other bookings.
- **Concurrency Handling**: Uses atomic transactions to prevent race conditions in high-concurrency environments.
- **Compatibility**: Designed to work with SQLite and other databases supported by Django.

## Requirements

- Python 3.6+
- Django 3.0+
- A supported database (SQLite, PostgreSQL, MySQL, etc.)

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/leon-rdo/appointment-scheduling-system.git
   cd appointment-scheduling-system
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (for admin access):

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:

   ```bash
   python manage.py runserver
   ```

## Usage

### Accessing the Admin Interface

- Navigate to `http://localhost:8000/admin/` and log in with the superuser credentials.
- You can manage users, professionals, and appointments from the admin panel.

### Booking an Appointment

1. **As a User**:

   - Register or log in to your user account.
   - Navigate to the appointment booking page.
   - Select the desired date and start time.
   - The system will automatically check for general availability.

2. **As the Management Team**:

   - Assign a professional to the appointment from the admin interface.
   - The system will check if the professional is available for the selected time and duration.

### Appointment Statuses

- **Pending (`'P'`)**: Default status when a user books an appointment.
- **Confirmed (`'C'`)**: Set by the management team after assigning a professional.
- **Cancelled (`'X'`)**: Can be set by the user or management team. Cancelled appointments are ignored in availability checks.

## Models

### Professional

Represents professionals who can be assigned to appointments.

```python
class Professional(models.Model):
    name = models.CharField('Name', max_length=100)
    is_active = models.BooleanField('Is active?', default=True)
```

### Appointment

Represents a user appointment.

```python
class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    professional = models.ForeignKey(Professional, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Professional')
    start_datetime = models.DateTimeField('Start DateTime')
    duration = models.DurationField('Duration', default=timedelta(hours=1, minutes=30))
    status = models.CharField(
        'Status',
        max_length=1,
        default='P',
        choices=[
            ('P', 'Pending'),
            ('C', 'Confirmed'),
            ('X', 'Cancelled')
        ]
    )
```

## Validation Logic

### General Availability Check

Ensures that the number of overlapping appointments does not exceed the number of active professionals.

```python
def check_general_availability(start_datetime, duration):
    professionals_count = Professional.objects.filter(is_active=True).count()
    end_datetime = start_datetime + duration

    overlapping_appointments = Appointment.objects.annotate(
        calculated_end_datetime=ExpressionWrapper(
            F('start_datetime') + F('duration'),
            output_field=DateTimeField()
        )
    ).filter(
        Q(start_datetime__lt=end_datetime),
        Q(calculated_end_datetime__gt=start_datetime),
        status__in=['P', 'C']
    ).count()

    return overlapping_appointments < professionals_count
```

### Professional Availability Check

Ensures that a specific professional is available for the desired time and duration.

```python
def is_professional_available(professional, start_datetime, duration):
    end_datetime = start_datetime + duration

    overlapping_appointments = Appointment.objects.filter(
        professional=professional,
        status__in=['P', 'C']
    ).annotate(
        calculated_end_datetime=ExpressionWrapper(
            F('start_datetime') + F('duration'),
            output_field=DateTimeField()
        )
    ).filter(
        Q(start_datetime__lt=end_datetime),
        Q(calculated_end_datetime__gt=start_datetime)
    )

    return not overlapping_appointments.exists()
```

### Appointment Clean Method

Validates appointments before saving.

```python
def clean(self):
    with transaction.atomic():
        if not self.pk:
            if not check_general_availability(self.start_datetime, self.duration):
                raise ValidationError('No professionals available at this time.')

        if self.professional and not is_professional_available(self.professional, self.start_datetime, self.duration):
            raise ValidationError('The selected professional is not available at this time.')
```

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**.
2. **Create a new branch** for your feature or bugfix.
3. **Commit your changes** with clear messages.
4. **Push to your fork** and submit a pull request.

Please ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Note**: This project is intended for educational purposes and may require further development for production use. Ensure to perform thorough testing and security assessments before deploying in a live environment.