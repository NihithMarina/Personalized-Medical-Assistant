import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prediction_engine import DiseasePredictionEngine

# Test the new prediction engine
engine = DiseasePredictionEngine()

print("Testing the new prediction engine...")
print("\nAvailable symptoms (first 20):")
symptoms = engine.get_available_symptoms()
for i, symptom in enumerate(symptoms[:20], 1):
    print(f"{i}. {symptom}")

print(f"\nTotal available symptoms: {len(symptoms)}")

# Test prediction
test_symptoms = ['fever', 'cough', 'headache']
print(f"\nTesting prediction with symptoms: {test_symptoms}")
result = engine.predict_disease(test_symptoms)
print(f"Predicted disease: {result['disease']}")
print(f"Confidence: {result['confidence']}%")
print(f"Medicines: {result['medicines']}")
print(f"Diet: {result['diet']}")

# Test with symptoms from the dataset
test_symptoms2 = ['itching', 'skin_rash', 'nodal_skin_eruptions']
print(f"\nTesting prediction with symptoms: {test_symptoms2}")
result2 = engine.predict_disease(test_symptoms2)
print(f"Predicted disease: {result2['disease']}")
print(f"Confidence: {result2['confidence']}%")
print(f"Medicines: {result2['medicines']}")
print(f"Diet: {result2['diet']}")