from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
import json

from .rf_prediction_engine import get_engine
from patients.models import DiseasePrediction

@login_required
def get_symptoms_api(request):
    """API endpoint to get available symptoms"""
    engine = get_engine()
    symptoms = engine.get_available_symptoms()
    return JsonResponse({'symptoms': symptoms})

@csrf_exempt
@login_required
def predict_disease_api(request):
    """API endpoint for disease prediction"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            symptoms = data.get('symptoms', [])
            
            if not symptoms:
                return JsonResponse({'error': 'No symptoms provided'}, status=400)
            
            engine = get_engine()
            result = engine.predict(symptoms)
            
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def prediction_detail(request, prediction_id):
    """View for detailed prediction information"""
    prediction = get_object_or_404(DiseasePrediction, id=prediction_id)
    
    # Check that user owns this prediction (if patient) or has access to patient (if doctor)
    user_can_view = False
    
    # If user is a patient, check if they own this prediction
    if request.user.groups.filter(name='Patients').exists():
        if prediction.patient.user == request.user:
            user_can_view = True
    
    # If user is a doctor, check if they have access to this patient
    # This would require additional logic to check if doctor has seen patient
    
    if not user_can_view:
        return render(request, '403.html', status=403)
    
    context = {
        'prediction': prediction,
    }
    
    return render(request, 'ml_prediction/prediction_detail.html', context)

@csrf_exempt
@login_required
def delete_prediction(request):
    """Delete a specific prediction for the current user"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prediction_id = data.get('prediction_id')
            
            if not prediction_id:
                return JsonResponse({'error': 'Prediction ID is required'}, status=400)
            
            # Get the prediction and ensure it belongs to the current user
            try:
                prediction = DiseasePrediction.objects.get(
                    id=prediction_id,
                    patient__user=request.user
                )
                prediction.delete()
                return JsonResponse({'success': True})
            except DiseasePrediction.DoesNotExist:
                return JsonResponse({'error': 'Prediction not found or access denied'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
@login_required
def delete_all_predictions(request):
    """Delete all predictions for the current user"""
    if request.method == 'POST':
        try:
            # Delete all predictions for the current user
            deleted_count = DiseasePrediction.objects.filter(
                patient__user=request.user
            ).delete()
            
            return JsonResponse({
                'success': True, 
                'deleted_count': deleted_count[0]
            })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)