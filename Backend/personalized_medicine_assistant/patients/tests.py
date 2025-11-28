"""
Unit tests for Patients app
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal

from .models import (
    PatientProfile, MedicineReminder, MedicalRecord, 
    Appointment, DiseasePrediction, Message, MessageEditHistory
)
from doctors.models import DoctorProfile, DoctorAvailability


class PatientProfileModelTest(TestCase):
    """Test PatientProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123'
        )
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.user.groups.add(patient_group)
    
    def test_patient_profile_creation(self):
        """Test creating a patient profile"""
        profile = PatientProfile.objects.create(
            user=self.user,
            full_name='Test Patient',
            age=30,
            height=170,
            weight=70,
            blood_group='O+'
        )
        self.assertEqual(str(profile), 'testpatient - Test Patient')
        self.assertIsNotNone(profile.bmi)
        self.assertIsNotNone(profile.bmi_status)
    
    def test_bmi_calculation(self):
        """Test BMI calculation and status"""
        # Test underweight
        profile = PatientProfile.objects.create(
            user=self.user,
            height=170,  # cm
            weight=50    # kg
        )
        self.assertAlmostEqual(profile.bmi, 17.30, places=1)
        self.assertEqual(profile.bmi_status, 'underweight')
        
        # Test normal weight
        profile.weight = 65
        profile.save()
        self.assertAlmostEqual(profile.bmi, 22.49, places=1)
        self.assertEqual(profile.bmi_status, 'normal')
        
        # Test overweight
        profile.weight = 80
        profile.save()
        self.assertAlmostEqual(profile.bmi, 27.68, places=1)
        self.assertEqual(profile.bmi_status, 'overweight')
        
        # Test obese
        profile.weight = 95
        profile.save()
        self.assertAlmostEqual(profile.bmi, 32.87, places=1)
        self.assertEqual(profile.bmi_status, 'obese')
    
    def test_patient_profile_update(self):
        """Test updating patient profile"""
        profile = PatientProfile.objects.create(user=self.user)
        profile.full_name = 'Updated Name'
        profile.age = 35
        profile.save()
        
        updated_profile = PatientProfile.objects.get(user=self.user)
        self.assertEqual(updated_profile.full_name, 'Updated Name')
        self.assertEqual(updated_profile.age, 35)


class MedicineReminderModelTest(TestCase):
    """Test MedicineReminder model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testpatient', password='testpass123')
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_medicine_reminder_creation(self):
        """Test creating a medicine reminder"""
        reminder = MedicineReminder.objects.create(
            patient=self.profile,
            medicine_name='Aspirin',
            dosage='100mg',
            frequency='twice',
            time_1=time(9, 0),
            time_2=time(21, 0),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
        self.assertEqual(str(reminder), 'Aspirin - testpatient')
        self.assertTrue(reminder.is_active)
    
    def test_medicine_reminder_frequency(self):
        """Test different frequency options"""
        for freq in ['once', 'twice', 'thrice', 'four']:
            reminder = MedicineReminder.objects.create(
                patient=self.profile,
                medicine_name=f'Medicine {freq}',
                dosage='100mg',
                frequency=freq,
                time_1=time(9, 0),
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7)
            )
            self.assertEqual(reminder.frequency, freq)


class MedicalRecordModelTest(TestCase):
    """Test MedicalRecord model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testpatient', password='testpass123')
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_medical_record_creation(self):
        """Test creating a medical record"""
        record = MedicalRecord.objects.create(
            patient=self.profile,
            title='Blood Test',
            record_type='lab_report',
            description='Routine blood test',
            date_created=date.today()
        )
        self.assertEqual(str(record), 'Blood Test - testpatient')
        self.assertEqual(record.record_type, 'lab_report')


class AppointmentModelTest(TestCase):
    """Test Appointment model"""
    
    def setUp(self):
        # Create patient
        patient_user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        patient_user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=patient_user)
        
        # Create doctor
        doctor_user = User.objects.create_user(username='doctor', password='pass123')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        doctor_user.groups.add(doctor_group)
        self.doctor = DoctorProfile.objects.create(
            user=doctor_user,
            full_name='Dr. Test',
            specialization='general'
        )
    
    def test_appointment_creation(self):
        """Test creating an appointment"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason='Regular checkup',
            status='pending'
        )
        self.assertEqual(appointment.status, 'pending')
        self.assertIn('patient', str(appointment))
        self.assertIn('doctor', str(appointment))
    
    def test_appointment_status_transitions(self):
        """Test appointment status changes"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason='Consultation'
        )
        
        # Test status transitions
        self.assertEqual(appointment.status, 'pending')
        
        appointment.status = 'accepted'
        appointment.save()
        self.assertEqual(appointment.status, 'accepted')
        
        appointment.status = 'completed'
        appointment.save()
        self.assertEqual(appointment.status, 'completed')


class DiseasePredictionModelTest(TestCase):
    """Test DiseasePrediction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='patient', password='pass123')
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_disease_prediction_creation(self):
        """Test creating a disease prediction"""
        prediction = DiseasePrediction.objects.create(
            patient=self.profile,
            symptoms='Fever, Cough, Headache',
            predicted_disease='Common Cold',
            confidence_score=0.85
        )
        self.assertEqual(prediction.predicted_disease, 'Common Cold')
        self.assertEqual(prediction.confidence_score, 0.85)
        self.assertIsNotNone(prediction.created_at)


class MessageModelTest(TestCase):
    """Test Message and MessageEditHistory models"""
    
    def setUp(self):
        # Create patient
        patient_user = User.objects.create_user(username='patient', password='pass123')
        self.patient = PatientProfile.objects.create(user=patient_user)
        
        # Create doctor
        doctor_user = User.objects.create_user(username='doctor', password='pass123')
        self.doctor = DoctorProfile.objects.create(user=doctor_user, full_name='Dr. Test')
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today(),
            appointment_time=time(10, 0),
            status='accepted'
        )
    
    def test_message_creation(self):
        """Test creating a message"""
        message = Message.objects.create(
            appointment=self.appointment,
            sender=self.patient.user,
            recipient=self.doctor.user,
            subject='Consultation',
            content='Hello Doctor'
        )
        self.assertEqual(message.content, 'Hello Doctor')
        self.assertFalse(message.is_edited)
    
    def test_message_edit(self):
        """Test editing a message"""
        message = Message.objects.create(
            appointment=self.appointment,
            sender=self.patient.user,
            recipient=self.doctor.user,
            subject='Question',
            content='Original message'
        )
        
        # Edit message
        message.content = 'Edited message'
        message.is_edited = True
        message.save()
        
        self.assertTrue(message.is_edited)
        self.assertEqual(message.content, 'Edited message')


class PatientViewsTest(TestCase):
    """Test Patient views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.user.groups.add(patient_group)
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_dashboard_access_authenticated(self):
        """Test dashboard access for authenticated patient"""
        self.client.login(username='patient', password='pass123')
        response = self.client.get('/patients/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_access_unauthenticated(self):
        """Test dashboard redirect for unauthenticated user"""
        response = self.client.get('/patients/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_profile_view(self):
        """Test patient profile view"""
        self.client.login(username='patient', password='pass123')
        response = self.client.get('/patients/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'patient')
    
    def test_edit_profile(self):
        """Test editing patient profile"""
        self.client.login(username='patient', password='pass123')
        response = self.client.post('/patients/profile/edit/', {
            'full_name': 'Test Patient',
            'age': 30,
            'height': 170,
            'weight': 70,
            'blood_group': 'O+',
            'medical_history': 'None',
            'allergies': 'None',
            'current_medications': 'None'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify profile was updated
        profile = PatientProfile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Test Patient')
        self.assertEqual(profile.age, 30)
