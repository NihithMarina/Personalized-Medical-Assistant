import pandas as pd
import numpy as np
from collections import defaultdict

# Load the dataset
df = pd.read_csv('data/dataset_with_recommendations.csv')

# Extract all symptoms from the dataset
all_symptoms = set()
symptom_columns = [f'Symptom_{i}' for i in range(1, 18)]

for col in symptom_columns:
    if col in df.columns:
        symptoms = df[col].dropna().str.strip().str.replace(' ', '')
        for symptom_list in symptoms:
            if symptom_list and symptom_list != '':
                # Split by comma and clean
                symptom_parts = [s.strip() for s in symptom_list.split(',') if s.strip()]
                for symptom in symptom_parts:
                    if symptom and len(symptom) > 1:
                        all_symptoms.add(symptom)

# Remove empty strings and clean up
all_symptoms = {s for s in all_symptoms if s and len(s) > 1}

print(f"Total unique symptoms found: {len(all_symptoms)}")
print("\nAll symptoms:")
for symptom in sorted(all_symptoms):
    print(f"- {symptom}")

# Categorize symptoms by body system
symptom_categories = {
    'Respiratory': [
        'cough', 'breathlessness', 'continuous_sneezing', 'runny_nose', 
        'congestion', 'sputum', 'phlegm', 'throat_irritation'
    ],
    'Gastrointestinal': [
        'vomiting', 'nausea', 'diarrhoea', 'loss_of_appetite', 'abdominal_pain',
        'stomach_pain', 'acidity', 'indigestion', 'constipation', 'passage_of_gases',
        'internal_itching', 'stomach_bleeding'
    ],
    'Neurological': [
        'headache', 'dizziness', 'loss_of_balance', 'lack_of_concentration',
        'visual_disturbances', 'altered_sensorium', 'weakness_of_one_body_side',
        'loss_of_smell', 'confusion', 'depression', 'anxiety'
    ],
    'Skin & External': [
        'itching', 'skin_rash', 'nodal_skin_eruptions', 'dischromic_patches',
        'yellowish_skin', 'yellowing_of_eyes', 'dark_urine', 'sweating',
        'dehydration', 'pus_filled_pimples', 'scurring', 'skin_peeling',
        'silver_like_dusting', 'small_dents_in_nails', 'inflammatory_nails'
    ],
    'General/Systemic': [
        'fever', 'chills', 'fatigue', 'weakness_in_limbs', 'high_fever',
        'sweating', 'dehydration', 'fast_heart_rate', 'muscle_weakness',
        'stiff_neck', 'swelling_joints', 'movement_stiffness', 'spinning_movements',
        'loss_of_balance', 'unsteadiness', 'weakness_of_one_body_side',
        'malaise', 'shivering'
    ],
    'Eyes & Vision': [
        'watering_from_eyes', 'sunken_eyes', 'yellowish_skin', 'yellowing_of_eyes',
        'visual_disturbances', 'blurred_and_distorted_vision', 'excessive_hunger',
        'increased_appetite', 'polyuria'
    ],
    'Musculoskeletal': [
        'joint_pain', 'muscle_pain', 'neck_pain', 'knee_pain', 'hip_joint_pain',
        'muscle_weakness', 'stiff_neck', 'swelling_joints', 'movement_stiffness',
        'painful_walking', 'muscle_wasting', 'weakness_in_limbs'
    ],
    'Urinary': [
        'burning_micturition', 'spotting_urination', 'dark_urine', 'polyuria',
        'bladder_discomfort', 'foul_smell_of_urine', 'continuous_feel_of_urine'
    ],
    'Mental/Cognitive': [
        'irritability', 'mood_swings', 'restlessness', 'lethargy', 'anxiety',
        'depression', 'confusion', 'coma', 'altered_sensorium', 'lack_of_concentration'
    ]
}

print("\n\nSymptoms by category:")
for category, symptoms in symptom_categories.items():
    print(f"\n{category}:")
    for symptom in symptoms:
        if symptom in all_symptoms:
            print(f"  ✓ {symptom}")
        else:
            print(f"  ✗ {symptom} (not in dataset)")