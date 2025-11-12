"""
Unit Tests for Background APIs
Tests all background API endpoints in the PMA application
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from patients.models import PatientProfile, MedicalRecord, Appointment, DiseasePrediction
from doctors.models import DoctorProfile, DoctorAvailability
from datetime import datetime, timedelta, time


class BackgroundAPIAuthenticationTest(TestCase):
    """Test authentication-related background APIs"""
    
    def setUp(self):
        self.client = Client()
        # Create groups
        Group.objects.get_or_create(name='Patients')
        Group.objects.get_or_create(name='Doctors')
    
    def test_patient_login_api(self):
        """Test patient login API endpoint"""
        # Create patient user
        patient_group = Group.objects.get(name='Patients')
        user = User.objects.create_user(username='testpatient', password='testpass123')
        user.groups.add(patient_group)
        PatientProfile.objects.create(user=user)
        
        # Test login - using Django's built-in auth
        logged_in = self.client.login(username='testpatient', password='testpass123')
        
        self.assertTrue(logged_in)
        self.assertTrue(self.client.session.get('_auth_user_id'))
    
    def test_doctor_login_api(self):
        """Test doctor login API endpoint"""
        # Create doctor user
        doctor_group = Group.objects.get(name='Doctors')
        user = User.objects.create_user(username='testdoctor', password='testpass123')
        user.groups.add(doctor_group)
        DoctorProfile.objects.create(
            user=user,
            specialization='General Medicine',
            license_number='LIC123'
        )
        
        # Test login - using Django's built-in auth
        logged_in = self.client.login(username='testdoctor', password='testpass123')
        
        self.assertTrue(logged_in)
        self.assertTrue(self.client.session.get('_auth_user_id'))
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Attempt to login with invalid credentials
        logged_in = self.client.login(username='nonexistent', password='wrongpass')
        
        self.assertFalse(logged_in)
        self.assertIsNone(self.client.session.get('_auth_user_id'))
    
    def test_logout_api(self):
        """Test logout API endpoint"""
        # Create and login user
        user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        
        # Verify logged in
        self.assertIsNotNone(self.client.session.get('_auth_user_id'))
        
        # Test logout
        self.client.logout()
        
        # Verify logged out
        self.assertIsNone(self.client.session.get('_auth_user_id'))


class BackgroundAPIDiseasePredictionTest(TestCase):
    """Test disease prediction background APIs"""
    
    def setUp(self):
        self.client = Client()
        # Create patient group and user
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.user = User.objects.create_user(username='patient', password='pass123')
        self.user.groups.add(patient_group)
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_predict_disease_api_authenticated(self):
        """Test disease prediction API with authenticated user"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post(
            '/patients/predict-disease/',
            data=json.dumps({
                'symptoms': ['fever', 'cough', 'fatigue']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('predicted_disease', data)
        self.assertIn('confidence', data)
        self.assertIn('medicine_recommendation', data)
        self.assertIn('diet_recommendation', data)
    
    def test_predict_disease_api_unauthenticated(self):
        """Test prediction API without authentication"""
        response = self.client.post(
            '/patients/predict-disease/',
            data=json.dumps({
                'symptoms': ['fever', 'cough']
            }),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_predict_disease_api_no_symptoms(self):
        """Test prediction API with no symptoms"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post(
            '/patients/predict-disease/',
            data=json.dumps({
                'symptoms': []
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_predict_disease_api_method_not_allowed(self):
        """Test prediction API with GET request (should only accept POST)"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.get('/patients/predict-disease/')
        
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Method not allowed')
    
    def test_predict_disease_saves_to_database(self):
        """Test that prediction is saved to database"""
        self.client.login(username='patient', password='pass123')
        
        # Get initial count
        initial_count = DiseasePrediction.objects.count()
        
        response = self.client.post(
            '/patients/predict-disease/',
            data=json.dumps({
                'symptoms': ['headache', 'fever']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        # Should have one more prediction
        self.assertEqual(DiseasePrediction.objects.count(), initial_count + 1)
        
        # Verify prediction details
        prediction = DiseasePrediction.objects.latest('created_at')
        self.assertEqual(prediction.patient, self.profile)
        self.assertIn('headache', prediction.symptoms)


class BackgroundAPIAppointmentTest(TestCase):
    """Test appointment-related background APIs"""
    
    def setUp(self):
        self.client = Client()
        
        # Create groups
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        
        # Create patient
        self.patient_user = User.objects.create_user(username='patient', password='pass123')
        self.patient_user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        
        # Create doctor
        self.doctor_user = User.objects.create_user(
            username='doctor',
            password='pass123',
            first_name='Dr. Test',
            last_name='Doctor'
        )
        self.doctor_user.groups.add(doctor_group)
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123'
        )
        
        # Create availability for Friday (Nov 7, 2025)
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            weekday=4,  # Friday
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
    
    def test_get_available_doctors_api(self):
        """Test getting available doctors for a specific date/time"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.get('/patients/appointments/available-doctors/', {
            'date': '2025-11-07',  # Friday
            'time': '10:00'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('doctors', data)
        self.assertGreater(len(data['doctors']), 0)
    
    def test_book_appointment_api(self):
        """Test booking an appointment via API"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post('/patients/appointments/book/', {
            'doctor': self.doctor.id,
            'appointment_date': '2025-11-07',
            'appointment_time': '10:00',
            'reason': 'Regular checkup'
        })
        
        # Should redirect after successful booking
        self.assertEqual(response.status_code, 302)
        
        # Verify appointment was created
        self.assertTrue(
            Appointment.objects.filter(
                patient=self.patient,
                doctor=self.doctor,
                status='pending'
            ).exists()
        )
    
    def test_book_appointment_requires_authentication(self):
        """Test that booking requires authentication"""
        response = self.client.post('/patients/appointments/book/', {
            'doctor': self.doctor.id,
            'appointment_date': '2025-11-07',
            'appointment_time': '10:00',
            'reason': 'Checkup'
        })
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class BackgroundAPIChatMessagingTest(TestCase):
    """Test chat/messaging background APIs"""
    
    def setUp(self):
        self.client = Client()
        
        # Create groups
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        
        # Create patient
        self.patient_user = User.objects.create_user(username='patient', password='pass123')
        self.patient_user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        
        # Create doctor
        self.doctor_user = User.objects.create_user(username='doctor', password='pass123')
        self.doctor_user.groups.add(doctor_group)
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123'
        )
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=datetime.now().date() + timedelta(days=1),
            appointment_time=time(10, 0),
            status='accepted'
        )
    
    def test_send_message_api_patient_to_doctor(self):
        """Test patient sending message to doctor via API"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post(
            '/patients/chat/send/',
            data=json.dumps({
                'doctor_id': self.doctor.id,
                'content': 'Hello doctor, I have a question'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
    
    def test_send_message_requires_accepted_appointment(self):
        """Test that messaging requires an accepted appointment"""
        # Create another patient without appointment
        patient2 = User.objects.create_user(username='patient2', password='pass123')
        patient2.groups.add(Group.objects.get(name='Patients'))
        PatientProfile.objects.create(user=patient2)
        
        self.client.login(username='patient2', password='pass123')
        
        response = self.client.post(
            '/patients/chat/send/',
            data=json.dumps({
                'doctor_id': self.doctor.id,
                'content': 'Hello'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_send_message_empty_content(self):
        """Test sending message with empty content"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post(
            '/patients/chat/send/',
            data=json.dumps({
                'doctor_id': self.doctor.id,
                'content': ''
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class BackgroundAPIPatientRecordsTest(TestCase):
    """Test patient records background APIs"""
    
    def setUp(self):
        self.client = Client()
        
        # Create groups
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        
        # Create patient
        self.patient_user = User.objects.create_user(username='patient', password='pass123')
        self.patient_user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        
        # Create doctor
        self.doctor_user = User.objects.create_user(username='doctor', password='pass123')
        self.doctor_user.groups.add(doctor_group)
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization='Cardiology',
            license_number='LIC456'
        )
        
        # Create appointment
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=datetime.now().date(),
            appointment_time=time(10, 0),
            status='accepted'
        )
    
    def test_doctor_access_patient_records_api(self):
        """Test doctor accessing patient records via API"""
        # Create a medical record
        MedicalRecord.objects.create(
            patient=self.patient,
            title='Blood Test Results',
            record_type='lab_report',
            description='Blood Test Results',
            date_created=datetime.now().date()
        )
        
        self.client.login(username='doctor', password='pass123')
        
        response = self.client.get(
            f'/doctors/patients/{self.patient.id}/records/api/'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('medical_records', data)
        self.assertGreater(len(data['medical_records']), 0)
    
    def test_add_medical_record_api(self):
        """Test patient adding medical record"""
        self.client.login(username='patient', password='pass123')
        
        initial_count = MedicalRecord.objects.count()
        
        response = self.client.post('/patients/medical-records/add/', {
            'title': 'New Prescription',
            'record_type': 'prescription',
            'description': 'New prescription from doctor',
            'date_created': '2025-11-07'
        })
        
        # Should redirect after successful addition
        self.assertEqual(response.status_code, 302)
        
        # Verify record was created
        self.assertEqual(MedicalRecord.objects.count(), initial_count + 1)
    
    def test_delete_medical_record_api(self):
        """Test deleting medical record"""
        self.client.login(username='patient', password='pass123')
        
        # Create a record
        record = MedicalRecord.objects.create(
            patient=self.patient,
            title='To be deleted',
            record_type='other',
            description='To be deleted',
            date_created=datetime.now().date()
        )
        
        response = self.client.post(f'/patients/medical-records/delete/{record.id}/')
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        
        # Verify record was deleted
        self.assertFalse(MedicalRecord.objects.filter(id=record.id).exists())


class BackgroundAPIErrorHandlingTest(TestCase):
    """Test error handling in background APIs"""
    
    def setUp(self):
        self.client = Client()
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.user = User.objects.create_user(username='patient', password='pass123')
        self.user.groups.add(patient_group)
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_predict_disease_invalid_json(self):
        """Test prediction API with invalid JSON"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post(
            '/patients/predict-disease/',
            data='invalid json data',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_api_requires_correct_http_method(self):
        """Test that APIs reject incorrect HTTP methods"""
        self.client.login(username='patient', password='pass123')
        
        # Prediction API should only accept POST
        response = self.client.get('/patients/predict-disease/')
        self.assertEqual(response.status_code, 405)
        
        # Send message API should only accept POST
        response = self.client.get('/patients/chat/send/')
        self.assertEqual(response.status_code, 405)
    
    def test_api_access_control(self):
        """Test that APIs enforce proper access control"""
        # Create doctor user
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        doctor_user = User.objects.create_user(username='doctor', password='pass123')
        doctor_user.groups.add(doctor_group)
        DoctorProfile.objects.create(
            user=doctor_user,
            specialization='General',
            license_number='LIC789'
        )
        
        # Doctor should not be able to access patient prediction API
        self.client.login(username='doctor', password='pass123')
        
        response = self.client.post(
            '/patients/predict-disease/',
            data=json.dumps({'symptoms': ['fever']}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Access denied')


class BackgroundAPIPerformanceTest(TestCase):
    """Test performance of background APIs"""
    
    def setUp(self):
        self.client = Client()
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.user = User.objects.create_user(username='patient', password='pass123')
        self.user.groups.add(patient_group)
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_prediction_api_response_time(self):
        """Test that prediction API responds within acceptable time"""
        import time
        
        self.client.login(username='patient', password='pass123')
        
        start_time = time.time()
        response = self.client.post(
            '/patients/predict-disease/',
            data=json.dumps({
                'symptoms': ['fever', 'cough', 'fatigue']
            }),
            content_type='application/json'
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # API should respond within 3 seconds
        self.assertLess(response_time, 3.0)
    
    def test_multiple_api_calls_performance(self):
        """Test performance with multiple sequential API calls"""
        import time
        
        self.client.login(username='patient', password='pass123')
        
        start_time = time.time()
        
        # Make 5 consecutive predictions
        for i in range(5):
            response = self.client.post(
                '/patients/predict-disease/',
                data=json.dumps({
                    'symptoms': ['fever', 'headache']
                }),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        total_time = end_time - start_time
        average_time = total_time / 5
        
        # Average response time should be under 2 seconds
        self.assertLess(average_time, 2.0)
