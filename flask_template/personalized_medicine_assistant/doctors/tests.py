"""
Unit tests for Doctors app
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal

from .models import DoctorProfile, DoctorAvailability
from patients.models import PatientProfile, Appointment


class DoctorProfileModelTest(TestCase):
    """Test DoctorProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            password='testpass123'
        )
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        self.user.groups.add(doctor_group)
    
    def test_doctor_profile_creation(self):
        """Test creating a doctor profile"""
        profile = DoctorProfile.objects.create(
            user=self.user,
            full_name='Dr. Test Doctor',
            specialization='cardiology',
            license_number='DOC12345',
            years_of_experience=10,
            consultation_fee=Decimal('500.00')
        )
        self.assertEqual(str(profile), 'Dr. Dr. Test Doctor - Cardiology')
        self.assertTrue(profile.is_available)
    
    def test_doctor_default_availability(self):
        """Test that new doctors are available by default"""
        profile = DoctorProfile.objects.create(
            user=self.user,
            full_name='Dr. Available',
            specialization='general'
        )
        self.assertTrue(profile.is_available)
    
    def test_doctor_experience_property(self):
        """Test the experience property alias"""
        profile = DoctorProfile.objects.create(
            user=self.user,
            years_of_experience=15
        )
        self.assertEqual(profile.experience, 15)
    
    def test_doctor_specialization_choices(self):
        """Test different specializations"""
        specializations = ['general', 'cardiology', 'dermatology', 'neurology']
        for spec in specializations:
            profile = DoctorProfile.objects.create(
                user=User.objects.create_user(username=f'doc_{spec}', password='pass123'),
                full_name=f'Dr. {spec.title()}',
                specialization=spec
            )
            self.assertEqual(profile.specialization, spec)


class DoctorAvailabilityModelTest(TestCase):
    """Test DoctorAvailability model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='doctor', password='pass123')
        self.doctor = DoctorProfile.objects.create(
            user=self.user,
            full_name='Dr. Test',
            specialization='general'
        )
    
    def test_availability_creation(self):
        """Test creating availability schedule"""
        availability = DoctorAvailability.objects.create(
            doctor=self.doctor,
            weekday=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        self.assertTrue(availability.is_active)
        self.assertIn('Monday', str(availability))
    
    def test_availability_multiple_days(self):
        """Test adding availability for multiple days"""
        days = [0, 1, 2, 3, 4]  # Monday to Friday
        for day in days:
            DoctorAvailability.objects.create(
                doctor=self.doctor,
                weekday=day,
                start_time=time(9, 0),
                end_time=time(17, 0)
            )
        
        availability_count = DoctorAvailability.objects.filter(doctor=self.doctor).count()
        self.assertEqual(availability_count, 5)
    
    def test_availability_unique_constraint(self):
        """Test that doctor can have only one availability per weekday"""
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        
        # Try to create duplicate - should raise exception
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            DoctorAvailability.objects.create(
                doctor=self.doctor,
                weekday=0,
                start_time=time(10, 0),
                end_time=time(18, 0)
            )


class DoctorViewsTest(TestCase):
    """Test Doctor views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='doctor', password='pass123')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        self.user.groups.add(doctor_group)
        self.profile = DoctorProfile.objects.create(
            user=self.user,
            full_name='Dr. Test',
            specialization='general'
        )
        
        # Create a patient for testing
        patient_user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        patient_user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=patient_user)
    
    def test_dashboard_access_authenticated(self):
        """Test dashboard access for authenticated doctor"""
        self.client.login(username='doctor', password='pass123')
        response = self.client.get('/doctors/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_access_unauthenticated(self):
        """Test dashboard redirect for unauthenticated user"""
        response = self.client.get('/doctors/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_profile_view(self):
        """Test doctor profile view"""
        self.client.login(username='doctor', password='pass123')
        response = self.client.get('/doctors/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr. Test')
    
    def test_edit_profile(self):
        """Test editing doctor profile"""
        self.client.login(username='doctor', password='pass123')
        response = self.client.post('/doctors/profile/edit/', {
            'full_name': 'Dr. Updated Name',
            'specialization': 'cardiology',
            'license_number': 'DOC12345',
            'years_of_experience': 10,
            'hospital_clinic': 'Test Hospital',
            'phone_number': '1234567890',
            'consultation_fee': '500.00',
            'about': 'Experienced cardiologist',
            'qualifications': 'MBBS, MD'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify profile was updated
        profile = DoctorProfile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Dr. Updated Name')
        self.assertEqual(profile.specialization, 'cardiology')
    
    def test_appointments_view(self):
        """Test doctor appointments view"""
        self.client.login(username='doctor', password='pass123')
        
        # Create test appointment
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.profile,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason='Checkup',
            status='pending'
        )
        
        response = self.client.get('/doctors/appointments/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Checkup')
    
    def test_accept_appointment(self):
        """Test accepting an appointment"""
        self.client.login(username='doctor', password='pass123')
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.profile,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason='Consultation',
            status='pending'
        )
        
        response = self.client.post(f'/doctors/appointments/accept/{appointment.id}/')
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify status changed
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'accepted')
    
    def test_reject_appointment(self):
        """Test rejecting an appointment"""
        self.client.login(username='doctor', password='pass123')
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.profile,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason='Consultation',
            status='pending'
        )
        
        response = self.client.post(
            f'/doctors/appointments/reject/{appointment.id}/',
            {'rejection_reason': 'Not available'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify status changed
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'rejected')
        self.assertEqual(appointment.doctor_notes, 'Not available')
    
    def test_availability_view(self):
        """Test doctor availability view"""
        self.client.login(username='doctor', password='pass123')
        response = self.client.get('/doctors/availability/')
        self.assertEqual(response.status_code, 200)
    
    def test_edit_availability(self):
        """Test editing doctor availability"""
        self.client.login(username='doctor', password='pass123')
        
        # Add availability for Monday
        response = self.client.post('/doctors/availability/edit/', {
            'start_time_0': '09:00',
            'end_time_0': '17:00',
            'available_0': 'on'
        })
        
        # Check if availability was created
        availability = DoctorAvailability.objects.filter(
            doctor=self.profile,
            weekday=0
        ).first()
        self.assertIsNotNone(availability)


class DoctorPatientInteractionTest(TestCase):
    """Test doctor-patient interactions"""
    
    def setUp(self):
        # Setup doctor
        doctor_user = User.objects.create_user(username='doctor', password='pass123')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        doctor_user.groups.add(doctor_group)
        self.doctor = DoctorProfile.objects.create(
            user=doctor_user,
            full_name='Dr. Test',
            specialization='general'
        )
        
        # Setup patient
        patient_user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        patient_user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=patient_user)
        
        self.client = Client()
    
    def test_patient_records_api_access(self):
        """Test doctor accessing patient records API"""
        self.client.login(username='doctor', password='pass123')
        
        response = self.client.get(f'/doctors/patients/{self.patient.id}/records/api/')
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        import json
        data = json.loads(response.content)
        self.assertIn('patient', data)
        self.assertIn('medical_records', data)
        self.assertIn('appointments', data)
    
    def test_complete_appointment(self):
        """Test doctor completing an appointment"""
        self.client.login(username='doctor', password='pass123')
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today(),
            appointment_time=time(10, 0),
            reason='Follow-up',
            status='accepted'
        )
        
        response = self.client.post(
            f'/doctors/appointments/complete/{appointment.id}/',
            {
                'doctor_notes': 'Patient is recovering well',
                'prescription': 'Continue current medications'
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify appointment completed
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'completed')
        self.assertIsNotNone(appointment.doctor_notes)
