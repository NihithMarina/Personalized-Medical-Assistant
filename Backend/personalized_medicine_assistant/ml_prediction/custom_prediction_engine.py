import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import difflib
import re

class CustomDiseasePredictionEngine:
    """
    Custom Disease Prediction Engine using the provided dataset
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
        
        # Load and prepare the dataset
        self._load_dataset()
        self._prepare_data()
        self._train_model()
    
    def _load_dataset(self):
        """Load the CSV dataset"""
        try:
            self.df = pd.read_csv(self.dataset_path)
            print(f"Dataset loaded successfully: {len(self.df)} rows, {len(self.df.columns)} columns")
        except Exception as e:
            print(f"Error loading dataset: {e}")
            raise
    
    def _prepare_data(self):
        """Prepare data for machine learning"""
        # Extract all unique symptoms from the dataset
        symptom_columns = [col for col in self.df.columns if col.startswith('Symptom_')]
        
        # Collect all unique symptoms
        all_symptoms = set()
        for col in symptom_columns:
            symptoms_in_col = self.df[col].dropna().astype(str)
            for symptom_row in symptoms_in_col:
                # Handle multiple symptoms in one cell (comma-separated)
                if ',' in symptom_row:
                    symptoms = [s.strip() for s in symptom_row.split(',')]
                    all_symptoms.update(symptoms)
                else:
                    all_symptoms.add(symptom_row.strip())
        
        # Clean symptoms (remove empty strings, normalize)
        self.symptoms_list = sorted([
            self._normalize_symptom(s) for s in all_symptoms 
            if s and s.strip() and s != 'nan'
        ])
        
        # Get unique diseases
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
        
        # Remove extra spaces and underscores
        symptom = re.sub(r'[_\s]+', ' ', symptom)
        
        # Replace spaces with underscores for consistency
        symptom = symptom.replace(' ', '_')
        
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
        X, y = self._prepare_training_data()
        
        if len(X) == 0:
            raise ValueError("No training data available")
        
        # Split data for training and testing
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Calculate accuracy
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model trained with accuracy: {accuracy:.2%}")
    
    def predict_disease(self, symptoms: List[str]) -> Dict[str, any]:
        """Predict disease based on symptoms"""
        if not symptoms:
            return {
                'disease': 'Unknown',
                'confidence': 0,
                'medicines': 'Consult a healthcare provider',
                'diet': 'Maintain a balanced diet'
            }
        
        # Normalize input symptoms
        normalized_symptoms = [self._normalize_symptom(s) for s in symptoms]
        
        # Create feature vector
        feature_vector = self._create_feature_vector(normalized_symptoms)
        
        # Get prediction
        predictions = self.model.predict_proba([feature_vector])[0]
        predicted_class_idx = np.argmax(predictions)
        predicted_disease = self.model.classes_[predicted_class_idx]
        confidence = predictions[predicted_class_idx] * 100
        
        # Get medicine and diet recommendations from dataset
        medicine_rec, diet_rec = self._get_recommendations(predicted_disease)
        
        return {
            'disease': predicted_disease,
            'confidence': round(confidence, 1),
            'medicines': medicine_rec,
            'diet': diet_rec
        }
    
    def _get_recommendations(self, disease: str) -> tuple:
        """Get medicine and diet recommendations for a disease"""
        disease_rows = self.df[self.df['Disease'] == disease]
        
        if not disease_rows.empty:
            # Get the first row's recommendations
            row = disease_rows.iloc[0]
            medicine = row.get('Medicine Recommendation', 'Consult a healthcare provider')
            diet = row.get('Diet Recommendation', 'Maintain a balanced diet')
            
            return str(medicine), str(diet)
        
        return 'Consult a healthcare provider', 'Maintain a balanced diet'
    
    def get_available_symptoms(self) -> List[str]:
        """Get list of all available symptoms"""
        # Convert back to readable format
        return [symptom.replace('_', ' ').title() for symptom in self.symptoms_list]
    
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
    
    def get_disease_info(self, disease: str) -> Dict[str, str]:
        """Get detailed information about a disease"""
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
                'medicines': str(row.get('Medicine Recommendation', 'Consult a healthcare provider')),
                'diet': str(row.get('Diet Recommendation', 'Maintain a balanced diet'))
            }
        
        return {
            'disease': disease,
            'symptoms': [],
            'medicines': 'Consult a healthcare provider',
            'diet': 'Maintain a balanced diet'
        }

# For backward compatibility, alias the class
DiseasePredictionEngine = CustomDiseasePredictionEngine