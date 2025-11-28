import os
import re
import csv
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import difflib
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import random

class EnhancedDiseasePredictionEngine:
    """
    Enhanced Disease Prediction Engine with categorized symptoms support
    """
    
    def __init__(self, dataset_path: Optional[str] = None):
        self.data_dir = Path(__file__).resolve().parent / 'data'
        
        if dataset_path:
            self.dataset_path = Path(dataset_path)
        else:
            self.dataset_path = self.data_dir / 'dataset_with_recommendations.csv'
        
        self.df = None
        self.model = None
        self.label_encoder = None
        self.symptoms_list = []
        self.diseases_list = []
        self.symptom_to_encoded = {}
        self.symptom_categories = self._get_symptom_categories()
        
        # Load and prepare the dataset
        self._load_dataset()
        self._prepare_data()
        self._train_model()
    
    def _get_symptom_categories(self) -> Dict[str, List[str]]:
        """Define comprehensive symptom categories based on the dataset"""
        return {
            'respiratory': [
                'cough', 'breathlessness', 'continuous_sneezing', 'chest_pain',
                'runny_nose', 'congestion', 'sputum', 'throat_irritation',
                'phlegm'
            ],
            'gastrointestinal': [
                'vomiting', 'nausea', 'diarrhoea', 'loss_of_appetite', 'abdominal_pain',
                'stomach_pain', 'acidity', 'indigestion', 'constipation', 'passage_of_gases',
                'internal_itching', 'ulcers_on_tongue', 'stomach_bleeding'
            ],
            'neurological': [
                'headache', 'dizziness', 'loss_of_balance', 'lack_of_concentration',
                'visual_disturbances', 'altered_sensorium', 'weakness_of_one_body_side',
                'loss_of_smell', 'blurred_and_distorted_vision', 'spinning_movements',
                'confusion', 'coma'
            ],
            'skin_external': [
                'itching', 'skin_rash', 'nodal_skin_eruptions', 'dischromic_patches',
                'yellowish_skin', 'yellowing_of_eyes', 'sweating', 'pus_filled_pimples',
                'scurring', 'skin_peeling', 'silver_like_dusting', 'small_dents_in_nails',
                'inflammatory_nails', 'blackheads'
            ],
            'general_systemic': [
                'fever', 'chills', 'fatigue', 'weakness_in_limbs', 'high_fever',
                'dehydration', 'fast_heart_rate', 'muscle_weakness', 'malaise',
                'shivering', 'unsteadiness', 'weight_loss', 'weight_gain',
                'increased_appetite', 'excessive_hunger'
            ],
            'musculoskeletal': [
                'joint_pain', 'muscle_pain', 'neck_pain', 'knee_pain', 'hip_joint_pain',
                'stiff_neck', 'swelling_joints', 'movement_stiffness', 'painful_walking',
                'muscle_wasting', 'back_pain', 'cramps'
            ],
            'urinary': [
                'burning_micturition', 'spotting_urination', 'dark_urine', 'polyuria',
                'bladder_discomfort', 'foul_smell_of_urine', 'continuous_feel_of_urine'
            ],
            'mental_cognitive': [
                'irritability', 'mood_swings', 'restlessness', 'lethargy', 'anxiety',
                'depression', 'confusion', 'coma', 'altered_sensorium', 'lack_of_concentration'
            ],
            'eyes_vision': [
                'watering_from_eyes', 'sunken_eyes', 'yellowish_skin', 'yellowing_of_eyes',
                'visual_disturbances', 'blurred_and_distorted_vision', 'excessive_hunger',
                'increased_appetite', 'polyuria'
            ]
        }
    
    def _load_dataset(self):
        """Load the CSV dataset"""
        try:
            self.df = pd.read_csv(self.dataset_path)
            print(f"Dataset loaded successfully: {len(self.df)} rows, {len(self.df.columns)} columns")
        except Exception as e:
            print(f"Error loading dataset: {e}")
            # Create fallback symptoms from categories
            self.symptoms_list = []
            for category_symptoms in self.symptom_categories.values():
                self.symptoms_list.extend(category_symptoms)
            self.df = None
    
    def _prepare_data(self):
        """Prepare data for machine learning"""
        if self.df is None:
            return
            
        # Extract all unique symptoms from the dataset
        symptom_columns = [col for col in self.df.columns if col.startswith('Symptom_')]
        
        # Collect all unique symptoms
        all_symptoms = set()
        for col in symptom_columns:
            symptoms_in_col = self.df[col].dropna().astype(str)
            for symptom_row in symptoms_in_col:
                # Handle multiple symptoms in one cell (comma-separated)
                if pd.notna(symptom_row) and str(symptom_row).strip() != 'nan':
                    if ',' in str(symptom_row):
                        symptoms = [s.strip() for s in str(symptom_row).split(',')]
                        for symptom in symptoms:
                            if symptom and symptom.strip():
                                all_symptoms.add(self._normalize_symptom(symptom))
                    else:
                        symptom = str(symptom_row).strip()
                        if symptom:
                            all_symptoms.add(self._normalize_symptom(symptom))
        
        # Clean symptoms (remove empty strings, normalize)
        self.symptoms_list = sorted([
            s for s in all_symptoms 
            if s and s.strip() and s != 'nan' and len(s) > 1
        ])
        
        # Get unique diseases
        if 'Disease' in self.df.columns:
            self.diseases_list = sorted(self.df['Disease'].unique())
        
        print(f"Found {len(self.symptoms_list)} unique symptoms")
        print(f"Found {len(self.diseases_list)} unique diseases")
        
        # Create symptom mapping
        self.symptom_to_encoded = {symptom: idx for idx, symptom in enumerate(self.symptoms_list)}
    
    def _normalize_symptom(self, symptom: str) -> str:
        """Normalize symptom names for consistency"""
        if not symptom or symptom == 'nan':
            return ''
        
        # Clean the symptom name
        symptom = str(symptom).strip().lower()
        
        # Remove extra spaces and special characters
        symptom = re.sub(r'[^\w\s]', '', symptom)
        symptom = re.sub(r'\s+', '_', symptom)
        
        return symptom
    
    def _create_feature_vector(self, symptoms: List[str]) -> np.ndarray:
        """Create a feature vector from symptoms list"""
        feature_vector = np.zeros(len(self.symptoms_list))
        
        normalized_symptoms = [self._normalize_symptom(s) for s in symptoms]
        
        for symptom in normalized_symptoms:
            if symptom in self.symptom_to_encoded:
                idx = self.symptom_to_encoded[symptom]
                feature_vector[idx] = 1
        
        return feature_vector
    
    def _prepare_training_data(self):
        """Prepare training data for the model"""
        X = []
        y = []
        
        symptom_columns = [col for col in self.df.columns if col.startswith('Symptom_')]
        
        for _, row in self.df.iterrows():
            # Extract symptoms for this row
            row_symptoms = []
            for col in symptom_columns:
                if pd.notna(row[col]):
                    symptom_value = str(row[col]).strip()
                    if symptom_value and symptom_value != 'nan':
                        # Handle comma-separated symptoms
                        if ',' in symptom_value:
                            symptoms = [s.strip() for s in symptom_value.split(',')]
                            row_symptoms.extend(symptoms)
                        else:
                            row_symptoms.append(symptom_value)
            
            if row_symptoms:  # Only add if we have symptoms
                feature_vector = self._create_feature_vector(row_symptoms)
                X.append(feature_vector)
                y.append(row['Disease'])
        
        return np.array(X), np.array(y)
    
    def _train_model(self):
        """Train the prediction model"""
        if self.df is None:
            print("Warning: No dataset available for training")
            return
            
        X, y = self._prepare_training_data()
        
        if len(X) == 0:
            print("Warning: No training data available")
            return
        
        # Split data for training and testing
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        self.model.fit(X_train, y_train)
        
        # Calculate accuracy
        if len(X_test) > 0:
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"Model trained with accuracy: {accuracy:.2%}")
    
    def predict_disease(self, symptoms: List[str], age: Optional[int] = None, gender: Optional[str] = None) -> Dict[str, any]:
        """Predict disease based on symptoms with enhanced response format"""
        if not symptoms:
            return {
                'predicted_disease': 'No symptoms provided',
                'confidence': 0,
                'medicine_recommendation': 'Please select symptoms to get a prediction',
                'diet_recommendation': 'Please select symptoms to get a prediction',
                'status': 'error'
            }
        
        if self.model is None or self.df is None:
            # Provide a more sophisticated fallback
            return self._fallback_prediction(symptoms, age, gender)
        
        try:
            # Normalize input symptoms
            normalized_symptoms = [self._normalize_symptom(s) for s in symptoms]
            
            # Create feature vector
            feature_vector = self._create_feature_vector(normalized_symptoms)
            
            # Get prediction
            predictions = self.model.predict_proba([feature_vector])[0]
            predicted_class_idx = np.argmax(predictions)
            predicted_disease = self.model.classes_[predicted_class_idx]
            confidence = predictions[predicted_class_idx]
            
            # Get recommendations
            medicine_rec, diet_rec = self._get_recommendations(predicted_disease)
            
            return {
                'predicted_disease': predicted_disease,
                'confidence': float(confidence),
                'medicine_recommendation': medicine_rec,
                'diet_recommendation': diet_rec,
                'status': 'success',
                'selected_symptoms': symptoms,
                'patient_info': {
                    'age': age,
                    'gender': gender
                }
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return self._fallback_prediction(symptoms, age, gender)
    
    def _fallback_prediction(self, symptoms: List[str], age: Optional[int] = None, gender: Optional[str] = None) -> Dict[str, any]:
        """Provide fallback prediction when model is not available"""
        # Simple rule-based prediction
        symptom_lower = [s.lower() for s in symptoms]
        
        if any(s in ['fever', 'cough', 'headache', 'fatigue'] for s in symptom_lower):
            return {
                'predicted_disease': 'Common Cold',
                'confidence': 0.75,
                'medicine_recommendation': 'Rest, plenty of fluids, paracetamol for fever',
                'diet_recommendation': 'Light foods, warm liquids, vitamin C rich foods',
                'status': 'fallback'
            }
        elif any(s in ['stomach_pain', 'nausea', 'vomiting'] for s in symptom_lower):
            return {
                'predicted_disease': 'Gastroenteritis',
                'confidence': 0.7,
                'medicine_recommendation': 'ORS, anti-emetics if needed, probiotics',
                'diet_recommendation': 'BRAT diet (Banana, Rice, Apple, Toast), clear fluids',
                'status': 'fallback'
            }
        else:
            return {
                'predicted_disease': 'General Illness',
                'confidence': 0.6,
                'medicine_recommendation': 'Consult a healthcare provider for proper diagnosis',
                'diet_recommendation': 'Maintain a balanced diet and stay hydrated',
                'status': 'fallback'
            }
    
    def _get_recommendations(self, disease: str) -> tuple:
        """Get medicine and diet recommendations for a disease"""
        if self.df is None:
            return 'Consult a healthcare provider', 'Maintain a balanced diet'
            
        disease_rows = self.df[self.df['Disease'] == disease]
        
        if not disease_rows.empty:
            # Get the first row's recommendations
            row = disease_rows.iloc[0]
            medicine = row.get('Medicine Recommendation', 'Consult a healthcare provider')
            diet = row.get('Diet Recommendation', 'Maintain a balanced diet')
            
            return str(medicine), str(diet)
        
        return 'Consult a healthcare provider', 'Maintain a balanced diet'
    
    def get_available_symptoms(self) -> List[str]:
        """Get list of all available symptoms organized by categories"""
        if not self.symptoms_list:
            # Return symptoms from categories
            all_symptoms = []
            for category_symptoms in self.symptom_categories.values():
                all_symptoms.extend(category_symptoms)
            return all_symptoms
        
        return self.symptoms_list
    
    def get_symptoms_by_category(self) -> Dict[str, List[str]]:
        """Get symptoms organized by categories"""
        categorized = {}
        
        for category, category_symptoms in self.symptom_categories.items():
            # Filter symptoms that exist in our dataset
            available_symptoms = []
            for symptom in category_symptoms:
                if symptom in self.symptoms_list or not self.symptoms_list:
                    available_symptoms.append(symptom)
            
            if available_symptoms:
                categorized[category] = available_symptoms
        
        return categorized
    
    def find_similar_symptoms(self, input_symptom: str, threshold: float = 0.6) -> List[str]:
        """Find similar symptoms using fuzzy matching"""
        normalized_input = self._normalize_symptom(input_symptom)
        matches = difflib.get_close_matches(
            normalized_input, 
            self.symptoms_list, 
            n=5, 
            cutoff=threshold
        )
        return [symptom.replace('_', ' ').title() for symptom in matches]
    
    def get_disease_info(self, disease: str) -> Dict[str, any]:
        """Get detailed information about a disease"""
        if self.df is None:
            return {
                'disease': disease,
                'symptoms': [],
                'medicine_recommendation': 'Consult a healthcare provider',
                'diet_recommendation': 'Maintain a balanced diet'
            }
            
        disease_rows = self.df[self.df['Disease'] == disease]
        
        if not disease_rows.empty:
            row = disease_rows.iloc[0]
            
            # Get common symptoms for this disease
            symptom_columns = [col for col in self.df.columns if col.startswith('Symptom_')]
            common_symptoms = []
            
            for col in symptom_columns:
                if pd.notna(row[col]):
                    symptom_value = str(row[col]).strip()
                    if symptom_value and symptom_value != 'nan':
                        if ',' in symptom_value:
                            symptoms = [s.strip() for s in symptom_value.split(',')]
                            common_symptoms.extend(symptoms)
                        else:
                            common_symptoms.append(symptom_value)
            
            return {
                'disease': disease,
                'symptoms': common_symptoms,
                'medicine_recommendation': str(row.get('Medicine Recommendation', 'Consult a healthcare provider')),
                'diet_recommendation': str(row.get('Diet Recommendation', 'Maintain a balanced diet'))
            }
        
        return {
            'disease': disease,
            'symptoms': [],
            'medicine_recommendation': 'Consult a healthcare provider',
            'diet_recommendation': 'Maintain a balanced diet'
        }

# Maintain backward compatibility
DiseasePredictionEngine = EnhancedDiseasePredictionEngine