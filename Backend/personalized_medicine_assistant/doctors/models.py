from django.db import models
from django.contrib.auth.models import User

class DoctorProfile(models.Model):
    SPECIALIZATION_CHOICES = [
        ('general', 'General Medicine'),
        ('cardiology', 'Cardiology'),
        ('dermatology', 'Dermatology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('psychiatry', 'Psychiatry'),
        ('surgery', 'Surgery'),
        ('gynecology', 'Gynecology'),
        ('oncology', 'Oncology'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    hospital_clinic = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    about = models.TextField(blank=True)
    qualifications = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Ensure new doctors are available by default
        if self.pk is None:
            self.is_available = True
        super().save(*args, **kwargs)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.full_name} - {self.get_specialization_display()}"

    @property
    def experience(self):
        """Compatibility property for templates that expect `profile.experience`.

        Internally the model stores years in `years_of_experience`, but some
        templates and forms use `experience`. Expose a read-only property so
        templates render correctly. Views will still write to
        `years_of_experience`.
        """
        return self.years_of_experience

class DoctorAvailability(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.doctor.full_name} - {self.get_weekday_display()}: {self.start_time}-{self.end_time}"
    
    class Meta:
        unique_together = ['doctor', 'weekday']