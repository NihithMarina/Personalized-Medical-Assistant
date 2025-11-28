from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, date
import json

from .models import PatientProfile, MedicineReminder, MedicalRecord, Appointment, DiseasePrediction, Message, MessageEditHistory
from doctors.models import DoctorProfile, DoctorAvailability
from ml_prediction.prediction_engine import DiseasePredictionEngine
from datetime import time as dt_time

# --- Helpers ---------------------------------------------------------------

def check_patient_access(request):
    """
    Helper function to check if user has patient access.
    Returns True if access granted, False otherwise.
    Automatically fixes group membership if profile exists.
    """
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to access this page.')
        return False
    
    user_groups = request.user.groups.values_list('name', flat=True)
    if 'Patients' not in user_groups:
        # Try to get the patient profile to check if user should be a patient
        try:
            PatientProfile.objects.get(user=request.user)
            # If profile exists, user should be in Patients group - fix it
            group, created = Group.objects.get_or_create(name='Patients')
            request.user.groups.add(group)
            return True
        except PatientProfile.DoesNotExist:
            messages.error(request, 'Access denied. You are not registered as a patient.')
            return False
    
    return True

def _parse_time_flexible(t: str) -> dt_time | None:
    """Parse a time string that may be in 24h (HH:MM) or 12h (h:MM AM/PM).

    Returns a datetime.time or None if parsing fails.
    """
    if not t:
        return None
    t = t.strip()
    # Normalize unicode whitespace
    t = " ".join(t.split())
    fmts = ["%H:%M", "%I:%M %p", "%H:%M:%S", "%I:%M:%S %p"]
    for fmt in fmts:
        try:
            return datetime.strptime(t, fmt).time()
        except Exception:
            continue
    # Try to salvage cases like '08:00PM' (missing space)
    if t.lower().endswith("am") or t.lower().endswith("pm"):
        t2 = t[:-2] + " " + t[-2:]
        for fmt in ("%I:%M %p", "%I:%M:%S %p"):
            try:
                return datetime.strptime(t2, fmt).time()
            except Exception:
                continue
    return None

# AJAX endpoint to get available doctors for a given date and time
@login_required
def get_available_doctors(request):
    if request.method == 'GET':
        appointment_date = request.GET.get('date')
        appointment_time = request.GET.get('time')
        filtered_doctors = []
        debug_log = []
        if appointment_date and appointment_time:
            weekday = datetime.strptime(appointment_date, "%Y-%m-%d").weekday()
            appt_time_obj = _parse_time_flexible(appointment_time)
            print(f"DEBUG: Checking for doctors available on weekday={weekday} (date={appointment_date}), time_raw={appointment_time}, time_parsed={appt_time_obj}")
            # Source of truth: active availability records that cover the selected time
            matching_avails = DoctorAvailability.objects.select_related('doctor').filter(
                weekday=weekday,
                is_active=True,
                start_time__lte=appt_time_obj,
                end_time__gte=appt_time_obj,
            ) if appt_time_obj is not None else DoctorAvailability.objects.none()

            seen_doctor_ids = set()
            for avail in matching_avails:
                doc = avail.doctor
                if doc.id in seen_doctor_ids:
                    continue
                seen_doctor_ids.add(doc.id)
                filtered_doctors.append({'id': doc.id, 'name': doc.full_name})
                debug_log.append({
                    'doctor': doc.full_name,
                    'weekday': weekday,
                    'appointment_time': str(appt_time_obj),
                    'matched_window': [str(avail.start_time), str(avail.end_time)],
                    'doctor_profile_is_available': doc.is_available,
                })
        # For debugging, include log in response
        return JsonResponse({'doctors': filtered_doctors, 'debug': debug_log})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, date
import json

from .models import PatientProfile, MedicineReminder, MedicalRecord, Appointment, DiseasePrediction
from doctors.models import DoctorProfile
from ml_prediction.prediction_engine import DiseasePredictionEngine

@login_required
def dashboard(request):
    """Patient dashboard view"""
    if not check_patient_access(request):
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    # Get recent data
    recent_predictions = DiseasePrediction.objects.filter(patient=profile).order_by('-created_at')[:3]
    
    # Get upcoming appointments (future dates only, excluding completed/cancelled)
    today = date.today()
    upcoming_appointments = Appointment.objects.filter(
        patient=profile, 
        appointment_date__gte=today
    ).exclude(
        status__in=['completed', 'cancelled']
    ).select_related('doctor__user').order_by('appointment_date', 'appointment_time')[:5]
    
    # Get recent completed appointments for medical summaries
    completed_appointments = Appointment.objects.filter(
        patient=profile,
        status='completed'
    ).select_related('doctor__user').order_by('-appointment_date', '-appointment_time')[:3]
    
    active_reminders = MedicineReminder.objects.filter(
        patient=profile, 
        is_active=True,
        end_date__gte=today
    )[:3]
    
    # Get total counts for stats
    total_predictions = DiseasePrediction.objects.filter(patient=profile).count()
    
    context = {
        'profile': profile,
        'recent_predictions': recent_predictions,
        'total_predictions': total_predictions,
        'upcoming_appointments': upcoming_appointments,
        'completed_appointments': completed_appointments,
        'active_reminders': active_reminders,
    }
    return render(request, 'patients/dashboard.html', context)

@login_required
def profile(request):
    """Patient profile view"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    # BMI recommendations
    bmi_recommendations = get_bmi_recommendations(profile.bmi_status)
    
    context = {
        'profile': profile,
        'bmi_recommendations': bmi_recommendations,
    }
    return render(request, 'patients/profile.html', context)

@login_required
def edit_profile(request):
    """Edit patient profile"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', '')
        profile.age = int(request.POST.get('age')) if request.POST.get('age') else None
        profile.height = float(request.POST.get('height')) if request.POST.get('height') else None
        profile.weight = float(request.POST.get('weight')) if request.POST.get('weight') else None
        profile.blood_group = request.POST.get('blood_group', '')
        profile.medical_history = request.POST.get('medical_history', '')
        profile.allergies = request.POST.get('allergies', '')
        profile.current_medications = request.POST.get('current_medications', '')
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('patients:profile')

    bmi = None
    bmi_status = None
    if profile.height and profile.weight:
        try:
            height_m = profile.height / 100.0
            bmi = profile.weight / (height_m ** 2)
            if bmi < 18.5:
                bmi_status = 'Underweight'
            elif bmi < 25:
                bmi_status = 'Normal weight'
            elif bmi < 30:
                bmi_status = 'Overweight'
            else:
                bmi_status = 'Obese'
        except Exception:
            bmi = None
            bmi_status = None

    return render(request, 'patients/edit_profile.html', {'profile': profile, 'bmi': bmi, 'bmi_status': bmi_status})

@login_required
def medicine_reminders(request):
    """Medicine reminders view"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    reminders = MedicineReminder.objects.filter(patient=profile).order_by('-created_at')
    
    return render(request, 'patients/medicine_reminders.html', {'reminders': reminders})

@login_required
def add_medicine_reminder(request):
    """Add medicine reminder"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        reminder = MedicineReminder(
            patient=profile,
            medicine_name=request.POST.get('medicine_name'),
            dosage=request.POST.get('dosage'),
            frequency=request.POST.get('frequency'),
            time_1=request.POST.get('time_1'),
            time_2=request.POST.get('time_2') if request.POST.get('time_2') else None,
            time_3=request.POST.get('time_3') if request.POST.get('time_3') else None,
            time_4=request.POST.get('time_4') if request.POST.get('time_4') else None,
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            notes=request.POST.get('notes', '')
        )
        reminder.save()
        messages.success(request, 'Medicine reminder added successfully!')
        return redirect('patients:medicine_reminders')
    
    return render(request, 'patients/add_medicine_reminder.html')

@login_required
def edit_medicine_reminder(request, reminder_id):
    """Edit medicine reminder"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    reminder = get_object_or_404(MedicineReminder, id=reminder_id, patient=profile)
    
    if request.method == 'POST':
        reminder.medicine_name = request.POST.get('medicine_name')
        reminder.dosage = request.POST.get('dosage')
        reminder.frequency = request.POST.get('frequency')
        reminder.time_1 = request.POST.get('time_1')
        reminder.time_2 = request.POST.get('time_2') if request.POST.get('time_2') else None
        reminder.time_3 = request.POST.get('time_3') if request.POST.get('time_3') else None
        reminder.time_4 = request.POST.get('time_4') if request.POST.get('time_4') else None
        reminder.start_date = request.POST.get('start_date')
        reminder.end_date = request.POST.get('end_date')
        reminder.notes = request.POST.get('notes', '')
        reminder.is_active = 'is_active' in request.POST
        
        reminder.save()
        messages.success(request, 'Medicine reminder updated successfully!')
        return redirect('patients:medicine_reminders')
    
    return render(request, 'patients/edit_medicine_reminder.html', {'reminder': reminder})

@login_required
def delete_medicine_reminder(request, reminder_id):
    """Delete medicine reminder"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    reminder = get_object_or_404(MedicineReminder, id=reminder_id, patient=profile)
    
    if request.method == 'POST':
        reminder.delete()
        messages.success(request, 'Medicine reminder deleted successfully!')
    
    return redirect('patients:medicine_reminders')

@login_required
def medical_records(request):
    """Medical records view"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    records = MedicalRecord.objects.filter(patient=profile).order_by('-date_created')
    
    return render(request, 'patients/medical_records.html', {'records': records})

@login_required
def add_medical_record(request):
    """Add medical record"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        record = MedicalRecord(
            patient=profile,
            title=request.POST.get('title'),
            record_type=request.POST.get('record_type'),
            description=request.POST.get('description', ''),
            date_created=request.POST.get('date_created')
        )
        
        if request.FILES.get('file'):
            record.file = request.FILES['file']
        
        record.save()
        messages.success(request, 'Medical record added successfully!')
        return redirect('patients:medical_records')
    
    return render(request, 'patients/add_medical_record.html')

@login_required
def delete_medical_record(request, record_id):
    """Delete medical record"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    record = get_object_or_404(MedicalRecord, id=record_id, patient=profile)
    
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Medical record deleted successfully!')
    
    return redirect('patients:medical_records')

@login_required
def appointments(request):
    """Appointments view"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    appointments = Appointment.objects.filter(patient=profile).select_related(
        'doctor__user'
    ).order_by('-appointment_date')
    
    # Calculate statistics
    total_appointments = appointments.count()
    pending_count = appointments.filter(status='pending').count()
    completed_count = appointments.filter(status='completed').count()
    confirmed_count = appointments.filter(status='accepted').count()
    
    context = {
        'appointments': appointments,
        'total_appointments': total_appointments,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'confirmed_count': confirmed_count,
    }
    
    return render(request, 'patients/appointments.html', context)

@login_required
def appointment_details(request, appointment_id):
    """View detailed appointment information including doctor's summary"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=profile)
    
    # Parse doctor notes to extract patient summary
    patient_summary = None
    diagnosis = None
    treatment_instructions = None
    follow_up_info = None
    
    if appointment.doctor_notes:
        notes = appointment.doctor_notes
        
        # Look for the patient summary section first
        if "=== PATIENT SUMMARY (SHARED) ===" in notes:
            summary_start = notes.find("=== PATIENT SUMMARY (SHARED) ===")
            if summary_start != -1:
                patient_summary = notes[summary_start + len("=== PATIENT SUMMARY (SHARED) ==="):].strip()
        
        # If no structured format, try to parse individual sections from the full notes
        if not patient_summary:
            patient_summary = notes  # Use full notes as fallback
        
        # Extract specific sections for better display
        if "DIAGNOSIS/CONDITION:" in notes:
            diag_start = notes.find("DIAGNOSIS/CONDITION:")
            if diag_start != -1:
                diag_section = notes[diag_start + len("DIAGNOSIS/CONDITION:"):].strip()
                diag_end = diag_section.find("\n\n")
                diagnosis = diag_section[:diag_end] if diag_end != -1 else diag_section
        
        if "TREATMENT INSTRUCTIONS:" in notes:
            treat_start = notes.find("TREATMENT INSTRUCTIONS:")
            if treat_start != -1:
                treat_section = notes[treat_start + len("TREATMENT INSTRUCTIONS:"):].strip()
                treat_end = treat_section.find("\n\n")
                treatment_instructions = treat_section[:treat_end] if treat_end != -1 else treat_section
        
        if "FOLLOW-UP REQUIRED:" in notes:
            follow_start = notes.find("FOLLOW-UP REQUIRED:")
            if follow_start != -1:
                follow_section = notes[follow_start + len("FOLLOW-UP REQUIRED:"):].strip()
                follow_end = follow_section.find("\n\n")
                follow_up_info = follow_section[:follow_end] if follow_end != -1 else follow_section
    
    context = {
        'appointment': appointment,
        'patient_summary': patient_summary,
        'diagnosis': diagnosis,
        'treatment_instructions': treatment_instructions,
        'follow_up_info': follow_up_info,
    }
    
    return render(request, 'patients/appointment_details.html', context)

@login_required
def book_appointment(request):
    """Book appointment with doctor"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    from doctors.models import DoctorAvailability
    import datetime
    # Pre-populate with any doctor who has at least one active availability,
    # regardless of the DoctorProfile.is_available flag (the time windows are the source of truth).
    filtered_doctors = DoctorProfile.objects.filter(doctoravailability__is_active=True).distinct()
    if request.method == 'POST':
        print('DEBUG POST DATA:', dict(request.POST))
        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        reason = request.POST.get('reason')
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        # Validate date and time
        if not appointment_date or not appointment_time:
            messages.error(request, 'Please select both date and time for your appointment.')
            return render(request, 'patients/book_appointment.html', {'doctors': filtered_doctors})
        # Parse time robustly and check availability using time objects
        appt_time_obj = _parse_time_flexible(appointment_time)
        if appt_time_obj is None:
            messages.error(request, 'Invalid time format. Please reselect the time.')
            return render(request, 'patients/book_appointment.html', {'doctors': filtered_doctors})
        # Check if doctor is available at the selected date and time
        weekday = datetime.datetime.strptime(appointment_date, "%Y-%m-%d").weekday()
        avail = DoctorAvailability.objects.filter(
            doctor=doctor,
            weekday=weekday,
            is_active=True,
            start_time__lte=appt_time_obj,
            end_time__gte=appt_time_obj
        ).first()
        if not avail:
            messages.error(request, 'Selected doctor is not available at the chosen time.')
            return render(request, 'patients/book_appointment.html', {'doctors': filtered_doctors})
        appointment = Appointment(
            patient=profile,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appt_time_obj,
            reason=reason
        )
        appointment.save()
        messages.success(request, 'Appointment booked successfully! Waiting for doctor approval.')
        return redirect('patients:appointments')
    else:
        # List doctors who have any active availability (distinct)
        pass
    return render(request, 'patients/book_appointment.html', {'doctors': filtered_doctors})

@login_required
def disease_prediction(request):
    """Patient-friendly Disease Prediction page with Random Forest ML"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    # Get available symptoms from the RF engine dataset
    try:
        from ml_prediction.rf_prediction_engine import get_engine
        engine = get_engine()
        available_symptoms = engine.get_available_symptoms()
        print(f"Successfully loaded {len(available_symptoms)} symptoms")
    except Exception as e:
        print(f"Error loading RF engine: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to basic symptoms
        available_symptoms = ['Fever', 'Cough', 'Headache', 'Fatigue', 'Nausea']
    
    context = {
        'recent_predictions': DiseasePrediction.objects.filter(patient=profile).order_by('-created_at')[:5],
        'available_symptoms': json.dumps(available_symptoms),
    }
    return render(request, 'patients/disease_prediction_new.html', context)


@csrf_exempt
@login_required
def predict_disease_api(request):
    """API endpoint for disease prediction (RandomForest primary)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    if not request.user.groups.filter(name='Patients').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    try:
        data = json.loads(request.body)
        symptoms = data.get('symptoms', [])
        age = data.get('age')  # reserved for future use
        gender = data.get('gender')  # reserved for future use
        if not symptoms:
            return JsonResponse({'error': 'No symptoms provided'}, status=400)
        # --- Random Forest Engine ---
        try:
            from ml_prediction.rf_prediction_engine import get_engine
            rf_engine = get_engine()
            result = rf_engine.predict(symptoms)
        except Exception as e:
            # Fallback chain
            try:
                from ml_prediction.prediction_engine import DiseasePredictionEngine
                legacy = DiseasePredictionEngine()
                legacy_res = legacy.predict_disease(symptoms)
                result = {
                    'predicted_disease': legacy_res.get('disease', 'Unknown'),
                    'confidence': legacy_res.get('confidence', 0),
                    'medicine_recommendation': legacy_res.get('medicines', ''),
                    'diet_recommendation': legacy_res.get('diet', ''),
                    'status': 'legacy_fallback',
                    'error': str(e)
                }
            except Exception as inner:
                return JsonResponse({'error': f'All engines failed: {inner}'}, status=500)
        # Persist
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        prediction = DiseasePrediction(
            patient=profile,
            symptoms=', '.join(symptoms),
            predicted_disease=result.get('predicted_disease', 'Unknown'),
            confidence_score=result.get('confidence', 0),
            recommended_medicines=result.get('medicine_recommendation', ''),
            recommended_diet=result.get('diet_recommendation', '')
        )
        prediction.save()
        return JsonResponse({
            'predicted_disease': result.get('predicted_disease', 'Unknown'),
            'confidence': result.get('confidence', 0),
            'medicine_recommendation': result.get('medicine_recommendation', 'Consult a healthcare provider'),
            'diet_recommendation': result.get('diet_recommendation', 'Maintain a balanced diet'),
            'status': result.get('status', 'success'),
            'candidates': result.get('candidates'),
            'prediction_id': prediction.id
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_bmi_recommendations(bmi_status):
    """Get BMI-based recommendations"""
    recommendations = {
        'underweight': {
            'diet': [
                'Increase calorie intake with healthy foods',
                'Include more proteins, nuts, and healthy fats',
                'Eat frequent small meals throughout the day',
                'Add dairy products and whole grains'
            ],
            'exercise': [
                'Focus on strength training exercises',
                'Include resistance training',
                'Avoid excessive cardio',
                'Get adequate rest for muscle recovery'
            ]
        },
        'normal': {
            'diet': [
                'Maintain a balanced diet',
                'Include variety of fruits and vegetables',
                'Stay hydrated with plenty of water',
                'Control portion sizes'
            ],
            'exercise': [
                'Regular aerobic exercise (150 min/week)',
                'Include strength training 2-3 times per week',
                'Stay active throughout the day',
                'Try different physical activities for variety'
            ]
        },
        'overweight': {
            'diet': [
                'Reduce calorie intake with portion control',
                'Focus on high-fiber, low-calorie foods',
                'Limit processed and sugary foods',
                'Increase water intake before meals'
            ],
            'exercise': [
                'Increase cardio exercises (walking, jogging)',
                'Include strength training to build muscle',
                'Aim for 300+ minutes of exercise per week',
                'Try low-impact activities like swimming'
            ]
        },
        'obese': {
            'diet': [
                'Create a significant calorie deficit',
                'Focus on whole, unprocessed foods',
                'Eat more vegetables and lean proteins',
                'Consider consulting a nutritionist'
            ],
            'exercise': [
                'Start with low-impact exercises',
                'Gradually increase exercise intensity',
                'Include both cardio and strength training',
                'Consider working with a fitness professional'
            ]
        }
    }
    
    return recommendations.get(bmi_status, {'diet': [], 'exercise': []})

@login_required
@csrf_exempt
def clear_all_predictions(request):
    """Clear all disease predictions for the current patient"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    if not request.user.groups.filter(name='Patients').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        deleted_count = DiseasePrediction.objects.filter(patient=profile).count()
        DiseasePrediction.objects.filter(patient=profile).delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully cleared {deleted_count} predictions',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def patient_chat(request):
    """Patient chat interface with doctors for accepted appointments"""
    if not request.user.groups.filter(name='Patients').exists():
        messages.error(request, 'Access denied. You are not a patient.')
        return redirect('home')
    
    patient_profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    # Get all accepted appointments with their doctors
    accepted_appointments = Appointment.objects.filter(
        patient=patient_profile,
        status='accepted'
    ).select_related('doctor__user').order_by('-created_at')
    
    # Get unique doctors from accepted appointments
    available_doctors = []
    seen_doctors = set()
    for appointment in accepted_appointments:
        doctor_id = appointment.doctor.id
        if doctor_id not in seen_doctors:
            seen_doctors.add(doctor_id)
            # Get latest message for this doctor-patient pair
            latest_message = Message.objects.filter(
                appointment__patient=patient_profile,
                appointment__doctor=appointment.doctor
            ).order_by('-created_at').first()
            
            available_doctors.append({
                'doctor': appointment.doctor,
                'latest_appointment': appointment,
                'latest_message': latest_message,
                'unread_count': Message.objects.filter(
                    appointment__patient=patient_profile,
                    appointment__doctor=appointment.doctor,
                    recipient=request.user,
                    is_read=False
                ).count()
            })
    
    context = {
        'available_doctors': available_doctors,
        'patient_profile': patient_profile,
    }
    return render(request, 'patients/chat.html', context)

@login_required
def get_chat_messages(request, doctor_id):
    """Get chat messages with a specific doctor"""
    if not request.user.groups.filter(name='Patients').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    patient_profile, created = PatientProfile.objects.get_or_create(user=request.user)
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    
    # Get messages for this doctor-patient pair from any accepted appointment
    # Exclude messages deleted for everyone or deleted for this user
    messages = Message.objects.filter(
        appointment__patient=patient_profile,
        appointment__doctor=doctor,
        appointment__status='accepted',
        is_deleted_for_everyone=False
    ).exclude(
        is_deleted=True, 
        recipient=request.user
    ).exclude(
        is_deleted=True,
        sender=request.user
    ).select_related('sender').order_by('created_at')
    
    # Mark received messages as read
    messages.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    message_list = []
    for msg in messages:
        message_list.append({
            'id': msg.id,
            'content': msg.content,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'is_sent': msg.sender == request.user,
            'is_edited': msg.is_edited,
            'edit_count': msg.edit_count,
            'created_at': msg.created_at.strftime('%H:%M'),
            'created_date': msg.created_at.strftime('%Y-%m-%d'),
            'created_timestamp': msg.created_at.isoformat(),
            'last_edited_at': msg.last_edited_at.strftime('%H:%M') if msg.last_edited_at else None,
            'last_edited_timestamp': msg.last_edited_at.isoformat() if msg.last_edited_at else None
        })
    
    return JsonResponse({'messages': message_list})

@login_required
def send_chat_message(request):
    """Send a chat message to a doctor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.groups.filter(name='Patients').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    import json
    data = json.loads(request.body)
    doctor_id = data.get('doctor_id')
    content = data.get('content', '').strip()
    
    if not doctor_id or not content:
        return JsonResponse({'error': 'Missing doctor_id or content'}, status=400)
    
    patient_profile, created = PatientProfile.objects.get_or_create(user=request.user)
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    
    # Find the most recent accepted appointment for this doctor-patient pair
    appointment = Appointment.objects.filter(
        patient=patient_profile,
        doctor=doctor,
        status='accepted'
    ).order_by('-created_at').first()
    
    if not appointment:
        return JsonResponse({'error': 'No accepted appointment found'}, status=400)
    
    # Create the message
    message = Message.objects.create(
        appointment=appointment,
        sender=request.user,
        recipient=doctor.user,
        subject='Chat Message',
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_name': message.sender.get_full_name() or message.sender.username,
            'is_sent': True,
            'created_at': message.created_at.strftime('%H:%M'),
            'created_date': message.created_at.strftime('%Y-%m-%d'),
            'created_timestamp': message.created_at.isoformat()
        }
    })

@login_required
def edit_message(request, message_id):
    """Edit a chat message (only by sender)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.groups.filter(name='Patients').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return JsonResponse({'error': 'Content cannot be empty'}, status=400)
        
        message = get_object_or_404(Message, id=message_id, sender=request.user)
        
        # Check if message was deleted
        if message.is_deleted_for_everyone:
            return JsonResponse({'error': 'Cannot edit deleted message'}, status=400)
        
        # Save edit history
        if message.content != new_content:
            MessageEditHistory.objects.create(
                message=message,
                previous_content=message.content,
                edited_by=request.user
            )
            
            # Update message
            if not message.original_content:
                message.original_content = message.content
            message.content = new_content
            message.is_edited = True
            message.edit_count += 1
            message.last_edited_at = timezone.now()
            message.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'is_edited': message.is_edited,
                'edit_count': message.edit_count,
                'last_edited_at': message.last_edited_at.strftime('%H:%M') if message.last_edited_at else None
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_message(request, message_id):
    """Delete a message with options for 'delete for me' or 'delete for everyone'"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.groups.filter(name='Patients').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        delete_type = data.get('delete_type', 'for_me')  # 'for_me' or 'for_everyone'
        
        message = get_object_or_404(Message, id=message_id)
        
        # Check if user has permission to delete
        if message.sender != request.user and message.recipient != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        if delete_type == 'for_everyone' and message.sender != request.user:
            return JsonResponse({'error': 'Only sender can delete for everyone'}, status=403)
        
        if delete_type == 'for_everyone':
            message.is_deleted_for_everyone = True
            message.deleted_by = request.user
            message.content = "This message was deleted"
        else:
            message.is_deleted = True
        
        message.save()
        
        return JsonResponse({
            'success': True,
            'delete_type': delete_type,
            'message_id': message.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def clear_chat(request, doctor_id):
    """Clear chat history with a specific doctor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.groups.filter(name='Patients').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        patient_profile = get_object_or_404(PatientProfile, user=request.user)
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        
        # Mark all messages as deleted for this user
        messages = Message.objects.filter(
            appointment__patient=patient_profile,
            appointment__doctor=doctor,
            appointment__status='accepted'
        )
        
        for message in messages:
            if message.sender == request.user:
                # If user is sender, they can choose to delete for everyone
                message.is_deleted_for_everyone = True
                message.deleted_by = request.user
                message.content = "This message was deleted"
            else:
                # If user is recipient, only delete for them
                message.is_deleted = True
            message.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Chat cleared successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)