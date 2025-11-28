"""
API Tests for all backend endpoints
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date, time, timedelta
import json

from patients.models import (
    PatientProfile, MedicalRecord, Appointment, 
    DiseasePrediction, Message
)
from doctors.models import DoctorProfile, DoctorAvailability


class AuthenticationAPITest(TestCase):
    """Test authentication related APIs"""
    
    def setUp(self):
        self.client = Client()
    
    def test_login_api_patient(self):
        """Test patient login"""
        user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        user.groups.add(patient_group)
        
        response = self.client.post('/login/', {
            'username': 'patient',
            'password': 'pass123',
            'user_type': 'patient'
        })
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn('/patients/dashboard/', response.url)
    
    def test_login_api_doctor(self):
        """Test doctor login"""
        user = User.objects.create_user(username='doctor', password='pass123')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        user.groups.add(doctor_group)
        
        response = self.client.post('/login/', {
            'username': 'doctor',
            'password': 'pass123',
            'user_type': 'doctor'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/doctors/dashboard/', response.url)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post('/login/', {
            'username': 'invalid',
            'password': 'wrong',
            'user_type': 'patient'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')
    
    def test_register_api_patient(self):
        """Test patient registration"""
        response = self.client.post('/register/', {
            'username': 'newpatient',
            'email': 'patient@test.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'user_type': 'patient'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Verify user created
        user = User.objects.get(username='newpatient')
        self.assertTrue(user.groups.filter(name='Patients').exists())
    
    def test_register_api_doctor(self):
        """Test doctor registration"""
        response = self.client.post('/register/', {
            'username': 'newdoctor',
            'email': 'doctor@test.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'user_type': 'doctor'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Verify user created
        user = User.objects.get(username='newdoctor')
        self.assertTrue(user.groups.filter(name='Doctors').exists())
    
    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post('/register/', {
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'pass123',
            'confirm_password': 'different',
            'user_type': 'patient'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'do not match')
    
    def test_logout_api(self):
        """Test logout"""
        user = User.objects.create_user(username='test', password='pass123')
        self.client.login(username='test', password='pass123')
        
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')


class AppointmentAPITest(TestCase):
    """Test appointment related APIs"""
    
    def setUp(self):
        self.client = Client()
        
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
        
        # Add doctor availability
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            weekday=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
    
    def test_book_appointment_api(self):
        """Test booking an appointment"""
        self.client.login(username='patient', password='pass123')
        
        # Find next Monday
        today = date.today()
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_monday = today + timedelta(days=days_ahead)
        
        response = self.client.post('/patients/appointments/book/', {
            'doctor': self.doctor.id,
            'appointment_date': next_monday.strftime('%Y-%m-%d'),
            'appointment_time': '10:00',
            'reason': 'Regular checkup'
        })
        
        # Should create appointment
        appointments = Appointment.objects.filter(patient=self.patient)
        self.assertGreater(appointments.count(), 0)
    
    def test_get_available_doctors_api(self):
        """Test getting available doctors for a date/time"""
        self.client.login(username='patient', password='pass123')
        
        today = date.today()
        response = self.client.get('/patients/appointments/available-doctors/', {
            'date': today.strftime('%Y-%m-%d'),
            'time': '10:00'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('doctors', data)
    
    def test_accept_appointment_api(self):
        """Test doctor accepting an appointment"""
        self.client.login(username='doctor', password='pass123')
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason='Consultation',
            status='pending'
        )
        
        response = self.client.post(f'/doctors/appointments/accept/{appointment.id}/')
        self.assertEqual(response.status_code, 302)
        
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'accepted')
    
    def test_reject_appointment_api(self):
        """Test doctor rejecting an appointment"""
        self.client.login(username='doctor', password='pass123')
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason='Consultation',
            status='pending'
        )
        
        response = self.client.post(
            f'/doctors/appointments/reject/{appointment.id}/',
            {'rejection_reason': 'Not available'}
        )
        
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'rejected')


class ChatAPITest(TestCase):
    """Test chat/messaging APIs"""
    
    def setUp(self):
        self.client = Client()
        
        # Create patient
        patient_user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        patient_user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=patient_user)
        
        # Create doctor
        doctor_user = User.objects.create_user(username='doctor', password='pass123')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        doctor_user.groups.add(doctor_group)
        self.doctor = DoctorProfile.objects.create(user=doctor_user, full_name='Dr. Test')
        
        # Create accepted appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today(),
            appointment_time=time(10, 0),
            status='accepted'
        )
    
    def test_send_message_doctor_to_patient(self):
        """Test doctor sending message to patient"""
        self.client.login(username='doctor', password='pass123')
        
        response = self.client.post(
            '/doctors/chat/send/',
            json.dumps({
                'patient_id': self.patient.id,
                'content': 'Hello, how are you feeling?'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify message created
        messages = Message.objects.filter(appointment=self.appointment)
        self.assertEqual(messages.count(), 1)
        self.assertEqual(messages.first().content, 'Hello, how are you feeling?')
    
    def test_send_message_patient_to_doctor(self):
        """Test patient sending message to doctor"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post(
            '/patients/chat/send/',
            json.dumps({
                'doctor_id': self.doctor.id,
                'content': 'I am feeling better, thank you!'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify message created
        messages = Message.objects.filter(appointment=self.appointment)
        self.assertEqual(messages.count(), 1)
    
    def test_get_chat_messages(self):
        """Test retrieving chat messages"""
        # Create some messages
        Message.objects.create(
            appointment=self.appointment,
            sender=self.doctor.user,
            recipient=self.patient.user,
            content='Doctor message'
        )
        Message.objects.create(
            appointment=self.appointment,
            sender=self.patient.user,
            recipient=self.doctor.user,
            content='Patient reply'
        )
        
        self.client.login(username='patient', password='pass123')
        response = self.client.get(f'/patients/chat/messages/{self.doctor.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('messages', data)
        self.assertEqual(len(data['messages']), 2)
    
    def test_edit_message(self):
        """Test editing a message"""
        message = Message.objects.create(
            appointment=self.appointment,
            sender=self.patient.user,
            recipient=self.doctor.user,
            content='Original message'
        )
        
        self.client.login(username='patient', password='pass123')
        response = self.client.post(
            f'/patients/chat/edit/{message.id}/',
            json.dumps({'content': 'Edited message'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        message.refresh_from_db()
        self.assertEqual(message.content, 'Edited message')
        self.assertTrue(message.is_edited)
    
    def test_delete_message(self):
        """Test deleting a message"""
        message = Message.objects.create(
            appointment=self.appointment,
            sender=self.patient.user,
            recipient=self.doctor.user,
            content='To be deleted'
        )
        
        self.client.login(username='patient', password='pass123')
        response = self.client.post(
            f'/patients/chat/delete/{message.id}/',
            data=json.dumps({'delete_type': 'for_me'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Message should be marked as deleted
        message.refresh_from_db()
        self.assertTrue(message.is_deleted)


class PatientRecordsAPITest(TestCase):
    """Test patient records APIs"""
    
    def setUp(self):
        self.client = Client()
        
        # Create patient
        patient_user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        patient_user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=patient_user)
        
        # Create doctor
        doctor_user = User.objects.create_user(username='doctor', password='pass123')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        doctor_user.groups.add(doctor_group)
        self.doctor = DoctorProfile.objects.create(user=doctor_user, full_name='Dr. Test')
    
    def test_doctor_access_patient_records_api(self):
        """Test doctor accessing patient records"""
        self.client.login(username='doctor', password='pass123')
        
        # Create medical record
        MedicalRecord.objects.create(
            patient=self.patient,
            title='Blood Test Results',
            record_type='lab_report',
            date_created=date.today()
        )
        
        response = self.client.get(f'/doctors/patients/{self.patient.id}/records/api/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('patient', data)
        self.assertIn('medical_records', data)
        self.assertEqual(len(data['medical_records']), 1)
    
    def test_add_medical_record_api(self):
        """Test patient adding medical record"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post('/patients/medical-records/add/', {
            'title': 'X-Ray Report',
            'record_type': 'scan',
            'description': 'Chest X-ray',
            'date_created': date.today().strftime('%Y-%m-%d')
        })
        
        # Should create record
        records = MedicalRecord.objects.filter(patient=self.patient)
        self.assertEqual(records.count(), 1)
        self.assertEqual(records.first().title, 'X-Ray Report')
    
    def test_delete_medical_record_api(self):
        """Test deleting medical record"""
        self.client.login(username='patient', password='pass123')
        
        record = MedicalRecord.objects.create(
            patient=self.patient,
            title='Old Record',
            record_type='other',
            date_created=date.today()
        )
        
        response = self.client.post(f'/patients/medical-records/delete/{record.id}/')
        
        # Record should be deleted
        with self.assertRaises(MedicalRecord.DoesNotExist):
            MedicalRecord.objects.get(id=record.id)


class DiseasePredictionAPITest(TestCase):
    """Test disease prediction APIs"""
    
    def setUp(self):
        self.client = Client()
        
        user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=user)
    
    def test_get_symptoms_api(self):
        """Test getting symptoms list"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.get('/predict/api/symptoms/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('symptoms', data)
        self.assertGreater(len(data['symptoms']), 0)
    
    def test_predict_disease_api(self):
        """Test disease prediction"""
        self.client.login(username='patient', password='pass123')
        
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        symptoms = engine.get_available_symptoms()[:3]
        
        if symptoms:
            response = self.client.post(
                '/patients/predict-disease/',
                json.dumps({'symptoms': symptoms}),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertIn('predicted_disease', data)
    
    def test_delete_prediction_api(self):
        """Test deleting a prediction"""
        self.client.login(username='patient', password='pass123')
        
        prediction = DiseasePrediction.objects.create(
            patient=self.patient,
            symptoms='Test',
            predicted_disease='Test Disease',
            confidence_score=0.8
        )
        
        response = self.client.post(
            '/predict/api/delete-prediction/',
            json.dumps({'prediction_id': prediction.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        with self.assertRaises(DiseasePrediction.DoesNotExist):
            DiseasePrediction.objects.get(id=prediction.id)
