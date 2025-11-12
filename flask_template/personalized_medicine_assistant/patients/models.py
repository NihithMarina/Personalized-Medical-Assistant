from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class PatientProfile(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    BMI_STATUS_CHOICES = [
        ('underweight', 'Underweight'),
        ('normal', 'Normal'),
        ('overweight', 'Overweight'),
        ('obese', 'Obese'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)], null=True, blank=True)
    height = models.FloatField(help_text="Height in cm", validators=[MinValueValidator(50), MaxValueValidator(250)], null=True, blank=True)
    weight = models.FloatField(help_text="Weight in kg", validators=[MinValueValidator(10), MaxValueValidator(300)], null=True, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    medical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    bmi = models.FloatField(null=True, blank=True)
    bmi_status = models.CharField(max_length=20, choices=BMI_STATUS_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate BMI and status if height and weight are provided
        if self.height and self.weight:
            height_m = self.height / 100  # Convert cm to meters
            self.bmi = round(self.weight / (height_m ** 2), 2)
            
            if self.bmi < 18.5:
                self.bmi_status = 'underweight'
            elif 18.5 <= self.bmi < 25:
                self.bmi_status = 'normal'
            elif 25 <= self.bmi < 30:
                self.bmi_status = 'overweight'
            else:
                self.bmi_status = 'obese'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.full_name}"

class MedicineReminder(models.Model):
    FREQUENCY_CHOICES = [
        ('once', 'Once a day'),
        ('twice', 'Twice a day'),
        ('thrice', 'Three times a day'),
        ('four', 'Four times a day'),
        ('custom', 'Custom'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    time_1 = models.TimeField()
    time_2 = models.TimeField(null=True, blank=True)
    time_3 = models.TimeField(null=True, blank=True)
    time_4 = models.TimeField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.medicine_name} - {self.patient.user.username}"

class MedicalRecord(models.Model):
    RECORD_TYPE_CHOICES = [
        ('lab_report', 'Lab Report'),
        ('prescription', 'Prescription'),
        ('scan', 'Medical Scan'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='medical_records/', null=True, blank=True)
    date_created = models.DateField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.patient.user.username}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey('doctors.DoctorProfile', on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    doctor_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient.user.username} - {self.doctor.user.username} - {self.appointment_date}"

class DiseasePrediction(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    symptoms = models.TextField()
    predicted_disease = models.CharField(max_length=200)
    confidence_score = models.FloatField()
    recommended_medicines = models.TextField()
    recommended_diet = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.patient.user.username} - {self.predicted_disease}"

class Message(models.Model):
    """Model for messages between patients and doctors"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    original_content = models.TextField(blank=True)  # Store original content before edits
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # Soft delete for sender
    is_deleted_for_everyone = models.BooleanField(default=False)  # Hard delete for everyone
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_messages')
    edit_count = models.PositiveIntegerField(default=0)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.subject}"
    
    @property
    def sender_type(self):
        """Determine if sender is patient or doctor"""
        if hasattr(self.sender, 'patientprofile'):
            return 'patient'
        elif hasattr(self.sender, 'doctorprofile'):
            return 'doctor'
        return 'admin'

class MessageEditHistory(models.Model):
    """Model to track message edit history"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='edit_history')
    previous_content = models.TextField()
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    edited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-edited_at']
    
    def __str__(self):
        return f"Edit #{self.id} for message {self.message.id} by {self.edited_by.username}"