from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q, F, ExpressionWrapper, DateTimeField
from datetime import timedelta


class Professional(models.Model):
    name = models.CharField('Name', max_length=100)
    is_active = models.BooleanField('Is active?', default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Professional'
        verbose_name_plural = 'Professionals'
        ordering = ['name']


def check_general_availability(start_datetime, duration):
    professionals_count = Professional.objects.filter(is_active=True).count()

    end_datetime = start_datetime + duration

    overlapping_appointments = Appointment.objects.annotate(
        calculated_end_datetime=ExpressionWrapper(
            F('start_datetime') + F('duration'),
            output_field=DateTimeField()
        )
    ).filter(
        Q(start_datetime__lt=end_datetime) & Q(calculated_end_datetime__gt=start_datetime),
        status__in=['P', 'C']
    ).count()

    return overlapping_appointments < professionals_count


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
        Q(start_datetime__lt=end_datetime) & Q(calculated_end_datetime__gt=start_datetime)
    )

    return not overlapping_appointments.exists()


class Appointment(models.Model):

    status_choices = [
        ('P', 'Pending'),
        ('C', 'Confirmed'),
        ('X', 'Cancelled')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    professional = models.ForeignKey(Professional, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Professional')
    start_datetime = models.DateTimeField('Start DateTime')
    duration = models.DurationField('Duration', default=timedelta(hours=1, minutes=30))
    status = models.CharField('Status', max_length=20, default='P', choices=status_choices)

    def __str__(self):
        return f'{self.start_datetime} - {self.user}'
    
    def clean(self):
        with transaction.atomic():
            if not self.pk:
                if not check_general_availability(self.start_datetime, self.duration):
                    raise ValidationError('No professionals available at this time.')

            if self.professional and not is_professional_available(self.professional, self.start_datetime, self.duration):
                raise ValidationError('The selected professional is not available at this time.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['start_datetime']
