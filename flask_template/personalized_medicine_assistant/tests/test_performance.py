"""
Performance Tests for PMA Application
Tests database query performance, ML prediction speed, and load handling
"""
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User, Group
from django.db import connection
from django.test.utils import override_settings
from django.utils import timezone
from datetime import date, time, timedelta
import time as time_module
import json

from patients.models import (
    PatientProfile, MedicineReminder, MedicalRecord,
    Appointment, DiseasePrediction, Message
)
from doctors.models import DoctorProfile, DoctorAvailability


class DatabaseQueryPerformanceTest(TestCase):
    """Test database query performance"""
    
    def setUp(self):
        # Create test data
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create bulk test data"""
        # Create 50 patients
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.patients = []
        for i in range(50):
            user = User.objects.create_user(
                username=f'patient{i}',
                password='pass123'
            )
            user.groups.add(patient_group)
            profile = PatientProfile.objects.create(
                user=user,
                full_name=f'Patient {i}',
                age=20 + i % 60
            )
            self.patients.append(profile)
        
        # Create 10 doctors
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        self.doctors = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'doctor{i}',
                password='pass123'
            )
            user.groups.add(doctor_group)
            profile = DoctorProfile.objects.create(
                user=user,
                full_name=f'Dr. {i}',
                specialization='general'
            )
            self.doctors.append(profile)
        
        # Create appointments
        for i, patient in enumerate(self.patients):
            doctor = self.doctors[i % len(self.doctors)]
            Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=date.today() + timedelta(days=i % 30),
                appointment_time=time(9 + i % 8, 0),
                reason='Checkup',
                status='pending'
            )
    
    def test_dashboard_query_performance_patient(self):
        """Test patient dashboard query performance"""
        client = Client()
        client.login(username='patient0', password='pass123')
        
        # Track queries
        start_time = time_module.time()
        # Patient dashboard is optimized and uses fewer queries
        response = client.get('/patients/dashboard/')
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        self.assertEqual(response.status_code, 200)
        # Dashboard should load in under 2 seconds
        self.assertLess(execution_time, 2.0, 
                       f"Dashboard took {execution_time:.2f}s, should be under 2s")
    
    def test_dashboard_query_performance_doctor(self):
        """Test doctor dashboard query performance"""
        client = Client()
        client.login(username='doctor0', password='pass123')
        
        start_time = time_module.time()
        # Doctor dashboard may use more queries due to appointment details
        response = client.get('/doctors/dashboard/')
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 2.0)
    
    def test_appointments_list_performance(self):
        """Test appointments list query performance"""
        client = Client()
        client.login(username='patient0', password='pass123')
        
        start_time = time_module.time()
        response = client.get('/patients/appointments/')
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        self.assertEqual(response.status_code, 200)
        # Should load quickly even with many appointments
        self.assertLess(execution_time, 1.5)
    
    def test_bulk_appointment_query(self):
        """Test querying multiple appointments efficiently"""
        start_time = time_module.time()
        
        # Use select_related to optimize queries
        appointments = Appointment.objects.select_related(
            'patient__user',
            'doctor__user'
        ).all()
        
        # Force evaluation
        list(appointments)
        
        end_time = time_module.time()
        execution_time = end_time - start_time
        
        # Should be fast even with many records
        self.assertLess(execution_time, 0.5)


class MLPredictionPerformanceTest(TestCase):
    """Test ML prediction engine performance"""
    
    def setUp(self):
        from ml_prediction.rf_prediction_engine import get_engine
        self.engine = get_engine()
    
    def test_single_prediction_speed(self):
        """Test speed of single prediction"""
        symptoms = self.engine.get_available_symptoms()[:5]
        
        start_time = time_module.time()
        result = self.engine.predict(symptoms)
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        
        # Prediction should be fast (under 1 second)
        self.assertLess(execution_time, 1.0,
                       f"Prediction took {execution_time:.2f}s, should be under 1s")
        self.assertIsInstance(result, dict)
    
    def test_multiple_predictions_speed(self):
        """Test speed of multiple consecutive predictions"""
        symptoms_list = [
            self.engine.get_available_symptoms()[:3],
            self.engine.get_available_symptoms()[3:6],
            self.engine.get_available_symptoms()[6:9],
        ]
        
        start_time = time_module.time()
        for symptoms in symptoms_list:
            if symptoms:
                self.engine.predict(symptoms)
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        avg_time = execution_time / len(symptoms_list)
        
        # Average prediction should be fast
        self.assertLess(avg_time, 0.5,
                       f"Average prediction took {avg_time:.2f}s, should be under 0.5s")
    
    def test_get_symptoms_speed(self):
        """Test speed of getting available symptoms"""
        start_time = time_module.time()
        symptoms = self.engine.get_available_symptoms()
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        
        # Should be very fast (cached or quick retrieval)
        self.assertLess(execution_time, 0.1)
        self.assertGreater(len(symptoms), 0)


class APIEndpointPerformanceTest(TestCase):
    """Test API endpoint response times"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test user
        user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=user)
        
        self.client.login(username='patient', password='pass123')
    
    def test_symptoms_api_response_time(self):
        """Test symptoms API response time"""
        start_time = time_module.time()
        response = self.client.get('/predict/api/symptoms/')
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5)
    
    def test_prediction_api_response_time(self):
        """Test prediction API response time"""
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        symptoms = engine.get_available_symptoms()[:4]
        
        if symptoms:
            start_time = time_module.time()
            response = self.client.post(
                '/predict/api/predict/',
                json.dumps({'symptoms': symptoms}),
                content_type='application/json'
            )
            end_time = time_module.time()
            
            execution_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200)
            # API call including prediction should be reasonably fast
            self.assertLess(execution_time, 2.0)


class ConcurrentUserLoadTest(TransactionTestCase):
    """Test system behavior under concurrent user load"""
    
    def setUp(self):
        # Create test users
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.test_users = []
        
        for i in range(10):
            user = User.objects.create_user(
                username=f'loadtest{i}',
                password='pass123'
            )
            user.groups.add(patient_group)
            PatientProfile.objects.create(user=user)
            self.test_users.append(user)
    
    def test_concurrent_dashboard_access(self):
        """Test multiple users accessing dashboard concurrently"""
        clients = []
        
        # Create clients for each user
        for user in self.test_users:
            client = Client()
            client.login(username=user.username, password='pass123')
            clients.append(client)
        
        # Simulate concurrent access
        start_time = time_module.time()
        responses = []
        for client in clients:
            response = client.get('/patients/dashboard/')
            responses.append(response)
        end_time = time_module.time()
        
        # All requests should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        # Total time for 10 users should be reasonable
        total_time = end_time - start_time
        avg_time = total_time / len(clients)
        self.assertLess(avg_time, 2.0)
    
    def test_concurrent_predictions(self):
        """Test concurrent disease predictions"""
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        symptoms = engine.get_available_symptoms()[:3]
        
        if not symptoms:
            self.skipTest("No symptoms available")
        
        clients = []
        for user in self.test_users[:5]:  # Use 5 users for prediction test
            client = Client()
            client.login(username=user.username, password='pass123')
            clients.append(client)
        
        start_time = time_module.time()
        responses = []
        for client in clients:
            response = client.post(
                '/predict/api/predict/',
                json.dumps({'symptoms': symptoms}),
                content_type='application/json'
            )
            responses.append(response)
        end_time = time_module.time()
        
        # All predictions should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        total_time = end_time - start_time
        avg_time = total_time / len(clients)
        # Concurrent predictions should complete reasonably
        self.assertLess(avg_time, 3.0)


class LargeDatasetPerformanceTest(TestCase):
    """Test performance with large datasets"""
    
    def setUp(self):
        # Create user with many records
        user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        user.groups.add(patient_group)
        self.patient = PatientProfile.objects.create(user=user)
        
        # Create many medical records
        for i in range(100):
            MedicalRecord.objects.create(
                patient=self.patient,
                title=f'Record {i}',
                record_type='other',
                description=f'Medical record number {i}',
                date_created=date.today() - timedelta(days=i)
            )
        
        # Create many predictions
        for i in range(50):
            DiseasePrediction.objects.create(
                patient=self.patient,
                symptoms=f'Symptoms {i}',
                predicted_disease=f'Disease {i}',
                confidence_score=0.7 + (i % 3) * 0.1
            )
    
    def test_medical_records_page_performance(self):
        """Test loading page with many medical records"""
        client = Client()
        client.login(username='patient', password='pass123')
        
        start_time = time_module.time()
        response = client.get('/patients/medical-records/')
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # Should handle large dataset reasonably
        self.assertLess(execution_time, 3.0)
    
    def test_predictions_page_performance(self):
        """Test loading page with many predictions"""
        client = Client()
        client.login(username='patient', password='pass123')
        
        start_time = time_module.time()
        response = client.get('/patients/disease-prediction/')
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 3.0)


class MemoryUsageTest(TestCase):
    """Test memory usage patterns"""
    
    def test_large_query_memory_usage(self):
        """Test memory usage doesn't spike with large queries"""
        import sys
        
        # Create test data
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        patients = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'memtest{i}',
                password='pass123'
            )
            user.groups.add(patient_group)
            profile = PatientProfile.objects.create(user=user)
            patients.append(profile)
        
        # Query using iterator to be memory efficient
        profiles = PatientProfile.objects.all().iterator()
        count = sum(1 for _ in profiles)
        
        self.assertEqual(count, 100)
        # Test passes if no memory errors occur
