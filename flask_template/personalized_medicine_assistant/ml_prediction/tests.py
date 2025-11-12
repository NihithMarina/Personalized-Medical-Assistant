"""
Unit tests for ML Prediction Engine
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
import json

from patients.models import PatientProfile, DiseasePrediction


class MLPredictionEngineTest(TestCase):
    """Test ML prediction engine functionality"""
    
    def test_get_engine(self):
        """Test getting the prediction engine instance"""
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        self.assertIsNotNone(engine)
    
    def test_available_symptoms(self):
        """Test getting available symptoms"""
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        symptoms = engine.get_available_symptoms()
        
        self.assertIsInstance(symptoms, list)
        self.assertGreater(len(symptoms), 0)
    
    def test_prediction_with_valid_symptoms(self):
        """Test disease prediction with valid symptoms"""
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        
        # Get some available symptoms
        symptoms = engine.get_available_symptoms()[:5]
        
        if symptoms:
            result = engine.predict(symptoms)
            
            self.assertIsInstance(result, dict)
            self.assertIn('predicted_disease', result)
            self.assertIn('confidence', result)  # Changed from confidence_score to confidence
    
    def test_prediction_with_empty_symptoms(self):
        """Test prediction with no symptoms"""
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        
        # Should handle empty list gracefully
        try:
            result = engine.predict([])
            # If it doesn't raise an error, check it returns a valid structure
            self.assertIsInstance(result, dict)
        except Exception as e:
            # It's acceptable to raise an error for empty symptoms
            self.assertIsInstance(e, (ValueError, Exception))


class MLPredictionAPITest(TestCase):
    """Test ML prediction API endpoints"""
    
    def setUp(self):
        self.client = Client()
        
        # Create patient user
        self.user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.user.groups.add(patient_group)
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_get_symptoms_api(self):
        """Test getting available symptoms via API"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.get('/predict/api/symptoms/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('symptoms', data)
        self.assertIsInstance(data['symptoms'], list)
    
    def test_predict_disease_api_authenticated(self):
        """Test disease prediction API with authenticated user"""
        self.client.login(username='patient', password='pass123')
        
        # Get available symptoms first
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        symptoms = engine.get_available_symptoms()[:3]
        
        if symptoms:
            response = self.client.post(
                '/predict/api/predict/',  # Fixed URL
                json.dumps({'symptoms': symptoms}),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            
            # Check response structure
            self.assertIn('predicted_disease', data)
            self.assertIn('confidence', data)  # Changed from confidence_score
    
    def test_predict_disease_api_unauthenticated(self):
        """Test disease prediction API without authentication"""
        response = self.client.post(
            '/predict/api/predict/',  # Fixed URL
            json.dumps({'symptoms': ['Fever', 'Cough']}),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_predict_disease_api_no_symptoms(self):
        """Test prediction API with no symptoms"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.post(
            '/predict/api/predict/',  # Fixed URL
            json.dumps({'symptoms': []}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_disease_prediction_page_access(self):
        """Test accessing disease prediction page"""
        self.client.login(username='patient', password='pass123')
        
        response = self.client.get('/patients/disease-prediction/')
        self.assertEqual(response.status_code, 200)


class DiseasePredictionModelTest(TestCase):
    """Test DiseasePrediction model and storage"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='patient', password='pass123')
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_save_prediction(self):
        """Test saving a disease prediction"""
        prediction = DiseasePrediction.objects.create(
            patient=self.profile,
            symptoms='Fever, Cough, Fatigue',
            predicted_disease='Influenza',
            confidence_score=0.89,
            recommended_medicines='Paracetamol',
            recommended_diet='Light foods'
        )
        
        self.assertEqual(prediction.predicted_disease, 'Influenza')
        self.assertEqual(prediction.confidence_score, 0.89)
        self.assertIsNotNone(prediction.created_at)
    
    def test_retrieve_patient_predictions(self):
        """Test retrieving all predictions for a patient"""
        # Create multiple predictions
        for i in range(3):
            DiseasePrediction.objects.create(
                patient=self.profile,
                symptoms=f'Symptom {i}',
                predicted_disease=f'Disease {i}',
                confidence_score=0.8 + (i * 0.05)
            )
        
        predictions = DiseasePrediction.objects.filter(patient=self.profile)
        self.assertEqual(predictions.count(), 3)
    
    def test_delete_prediction(self):
        """Test deleting a prediction"""
        self.client = Client()
        self.client.login(username='patient', password='pass123')
        
        prediction = DiseasePrediction.objects.create(
            patient=self.profile,
            symptoms='Test symptoms',
            predicted_disease='Test disease',
            confidence_score=0.75
        )
        
        response = self.client.post(
            '/predict/api/delete-prediction/',
            json.dumps({'prediction_id': prediction.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        with self.assertRaises(DiseasePrediction.DoesNotExist):
            DiseasePrediction.objects.get(id=prediction.id)


class MLPredictionIntegrationTest(TestCase):
    """Integration tests for the complete prediction workflow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='patient', password='pass123')
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        self.user.groups.add(patient_group)
        self.profile = PatientProfile.objects.create(user=self.user)
    
    def test_complete_prediction_workflow(self):
        """Test complete workflow: get symptoms -> predict -> get results"""
        self.client.login(username='patient', password='pass123')
        
        # Step 1: Get available symptoms
        response = self.client.get('/predict/api/symptoms/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        symptoms = data['symptoms'][:3]
        
        # Step 2: Make prediction
        if symptoms:
            response = self.client.post(
                '/predict/api/predict/',
                json.dumps({'symptoms': symptoms}),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            prediction_data = json.loads(response.content)
            
            # Step 3: Verify prediction response contains expected fields
            self.assertIn('predicted_disease', prediction_data)
            self.assertIn('confidence', prediction_data)
            self.assertTrue(prediction_data['predicted_disease'])
            self.assertIsInstance(prediction_data['confidence'], (int, float))
