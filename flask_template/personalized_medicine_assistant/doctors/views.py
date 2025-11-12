
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, date, time, timedelta
import json

from .models import DoctorProfile, DoctorAvailability
from patients.models import Appointment, PatientProfile, DiseasePrediction, MedicalRecord, Message, MessageEditHistory

# --- Helpers ---------------------------------------------------------------

def check_doctor_access(request):
    """
    Helper function to check if user has doctor access.
    Returns True if access granted, False otherwise.
    Automatically fixes group membership if profile exists.
    """
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to access this page.')
        return False
    
    user_groups = request.user.groups.values_list('name', flat=True)
    if 'Doctors' not in user_groups:
        # Try to get the doctor profile to check if user should be a doctor
        try:
            DoctorProfile.objects.get(user=request.user)
            # If profile exists, user should be in Doctors group - fix it
            group, created = Group.objects.get_or_create(name='Doctors')
            request.user.groups.add(group)
            return True
        except DoctorProfile.DoesNotExist:
            messages.error(request, 'Access denied. You are not registered as a doctor.')
            return False
    
    return True

# Debug view: show all doctors and their availability
@login_required
def debug_doctor_availability(request):
    doctors = DoctorProfile.objects.all()
    data = []
    for doc in doctors:
        availabilities = DoctorAvailability.objects.filter(doctor=doc)
        avails = []
        for avail in availabilities:
            avails.append({
                'weekday': avail.get_weekday_display(),
                'start_time': str(avail.start_time),
                'end_time': str(avail.end_time),
                'is_active': avail.is_active
            })
        data.append({'doctor': doc.full_name, 'availabilities': avails})
    return JsonResponse({'doctors': data})

@login_required
def dashboard(request):
    """Enhanced doctor dashboard view with analytics"""
    if not check_doctor_access(request):
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    # Get dashboard analytics
    pending_appointments = Appointment.objects.filter(
        doctor=profile, 
        status='pending'
    ).count()
    
    todays_appointments_count = Appointment.objects.filter(
        doctor=profile,
        appointment_date=date.today(),
        status='accepted'
    ).count()
    
    todays_appointments = Appointment.objects.filter(
        doctor=profile,
        appointment_date=date.today(),
        status='accepted'
    ).order_by('appointment_time')
    
    recent_appointments = Appointment.objects.filter(
        doctor=profile
    ).order_by('-created_at')[:5]
    
    total_patients = Appointment.objects.filter(
        doctor=profile,
        status__in=['accepted', 'completed']
    ).values('patient').distinct().count()
    
    # Get AI prediction analytics
    one_week_ago = timezone.now() - timedelta(days=7)
    recent_predictions_count = DiseasePrediction.objects.filter(
        created_at__gte=one_week_ago
    ).count()
    
    # Get recent patient predictions for the notification panel
    recent_patient_predictions = DiseasePrediction.objects.select_related('patient').filter(
        created_at__gte=one_week_ago
    ).order_by('-created_at')[:5]
    
    # Priority alerts calculations
    pending_urgent_appointments = Appointment.objects.filter(
        doctor=profile,
        status='pending',
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    # Simulated data for unread messages and follow-ups (can be enhanced later)
    unread_messages = 0  # To be implemented with messaging system
    follow_up_due = Appointment.objects.filter(
        doctor=profile,
        status='completed',
        appointment_date__gte=date.today() - timedelta(days=14),
        appointment_date__lte=date.today() - timedelta(days=7)
    ).count()
    
    context = {
        'profile': profile,
        'pending_appointments': pending_appointments,
        'todays_appointments': todays_appointments,
        'todays_appointments_count': todays_appointments_count,
        'recent_appointments': recent_appointments,
        'total_patients': total_patients,
        'recent_predictions': recent_predictions_count,
        'recent_patient_predictions': recent_patient_predictions,
        'pending_requests': pending_appointments,
        'pending_urgent_appointments': pending_urgent_appointments,
        'unread_messages': unread_messages,
        'follow_up_due': follow_up_due,
        'availability': DoctorAvailability.objects.filter(doctor=profile, is_active=True).order_by('weekday', 'start_time'),
    }
    return render(request, 'doctors/dashboard.html', context)

@login_required
def patients(request):
    """Patient records view"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied. You are not a doctor.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    # Get all patients who have appointments with this doctor
    patient_appointments = Appointment.objects.filter(
        doctor=profile,
        status__in=['accepted', 'completed']
    ).select_related('patient__user').order_by('-appointment_date')
    
    # Group by patient to avoid duplicates and get latest appointment info
    patients_data = {}
    for appointment in patient_appointments:
        patient_id = appointment.patient.id
        if patient_id not in patients_data:
            # Get medical records count for this patient
            medical_records_count = MedicalRecord.objects.filter(
                patient=appointment.patient
            ).count()
            
            patients_data[patient_id] = {
                'patient': appointment.patient,
                'latest_appointment': appointment,
                'total_appointments': patient_appointments.filter(patient=appointment.patient).count(),
                'medical_records_count': medical_records_count,
                'last_visit': appointment.appointment_date,
            }
    
    # Convert to list for template
    patients_list = list(patients_data.values())
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        patients_list = [
            p for p in patients_list 
            if search_query.lower() in p['patient'].full_name.lower() or 
               search_query.lower() in p['patient'].user.username.lower()
        ]
    
    context = {
        'patients': patients_list,
        'search_query': search_query,
        'total_patients': len(patients_list),
    }
    return render(request, 'doctors/patients.html', context)

@login_required
def profile(request):
    """Doctor profile view"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    availability = DoctorAvailability.objects.filter(doctor=profile, is_active=True)
    
    context = {
        'profile': profile,
        'availability': availability,
    }
    return render(request, 'doctors/profile.html', context)

@login_required
def edit_profile(request):
    """Edit doctor profile"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', '')
        profile.specialization = request.POST.get('specialization', '')
        profile.license_number = request.POST.get('license_number', '')
        # Support templates that use 'experience' as the field name
        exp_val = request.POST.get('years_of_experience') or request.POST.get('experience')
        try:
            profile.years_of_experience = int(exp_val) if exp_val is not None and exp_val != '' else 0
        except (ValueError, TypeError):
            profile.years_of_experience = 0
        profile.qualifications = request.POST.get('qualifications', '')
        profile.hospital_clinic = request.POST.get('hospital_clinic', '')
        profile.address = request.POST.get('address', '')
        profile.phone_number = request.POST.get('phone_number', '')
        profile.consultation_fee = float(request.POST.get('consultation_fee', 0))
        profile.about = request.POST.get('about', '')
        profile.is_available = 'is_available' in request.POST
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('doctors:profile')
    
    return render(request, 'doctors/edit_profile.html', {'profile': profile})

@login_required
def appointments(request):
    """Doctor appointments view"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    # Filter appointments by status
    status_filter = request.GET.get('status', 'all')
    appointments = Appointment.objects.filter(doctor=profile)
    
    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)
    
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    context = {
        'appointments': appointments,
        'status_filter': status_filter,
    }
    return render(request, 'doctors/appointments.html', context)

@login_required
def accept_appointment(request, appointment_id):
    """Accept appointment request"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=profile)
    
    if appointment.status == 'pending':
        appointment.status = 'accepted'
        appointment.save()
        messages.success(request, 'Appointment accepted successfully!')
    else:
        messages.error(request, 'Appointment cannot be accepted.')
    
    return redirect('doctors:appointments')

@login_required
def reject_appointment(request, appointment_id):
    """Reject appointment request"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=profile)
    
    if request.method == 'POST':
        if appointment.status == 'pending':
            appointment.status = 'rejected'
            appointment.doctor_notes = request.POST.get('rejection_reason', '')
            appointment.save()
            messages.success(request, 'Appointment rejected successfully!')
        else:
            messages.error(request, 'Appointment cannot be rejected.')
        
        return redirect('doctors:appointments')
    
    return render(request, 'doctors/reject_appointment.html', {'appointment': appointment})

@login_required
def complete_appointment(request, appointment_id):
    """Mark appointment as completed"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=profile)
    
    if request.method == 'POST':
        if appointment.status == 'accepted':
            appointment.status = 'completed'
            
            # Collect form data
            private_notes = request.POST.get('appointment_notes', '')
            diagnosis = request.POST.get('diagnosis', '')
            patient_instructions = request.POST.get('patient_instructions', '')
            follow_up = request.POST.get('follow_up', '')
            follow_up_notes = request.POST.get('follow_up_notes', '')
            
            # Structure the notes with clear separation
            structured_notes = []
            
            # PRIVATE SECTION (Doctor only)
            if private_notes:
                structured_notes.append(f"=== PRIVATE MEDICAL NOTES (DOCTOR ONLY) ===\n{private_notes}")
            
            # PATIENT SUMMARY SECTION (Shared with patient)
            patient_summary = []
            if diagnosis:
                patient_summary.append(f"DIAGNOSIS/CONDITION:\n{diagnosis}")
            
            if patient_instructions:
                patient_summary.append(f"TREATMENT INSTRUCTIONS:\n{patient_instructions}")
            
            if follow_up:
                follow_up_text = {
                    'none': 'No follow-up needed',
                    '1_week': 'Follow-up in 1 week',
                    '2_weeks': 'Follow-up in 2 weeks', 
                    '1_month': 'Follow-up in 1 month',
                    '3_months': 'Follow-up in 3 months',
                    'as_needed': 'Follow-up as needed'
                }.get(follow_up, follow_up)
                
                follow_up_section = f"FOLLOW-UP REQUIRED:\n{follow_up_text}"
                if follow_up_notes:
                    follow_up_section += f"\n\nFOLLOW-UP INSTRUCTIONS:\n{follow_up_notes}"
                patient_summary.append(follow_up_section)
            
            if patient_summary:
                structured_notes.append(f"=== PATIENT SUMMARY (SHARED) ===\n" + '\n\n'.join(patient_summary))
            
            # Join all sections
            appointment.doctor_notes = '\n\n'.join(structured_notes)
            appointment.save()
            
            messages.success(request, 'Appointment completed successfully! Patient summary has been recorded.')
        else:
            messages.error(request, 'Appointment cannot be completed.')
        
        return redirect('doctors:appointments')
    
    return render(request, 'doctors/complete_appointment.html', {'appointment': appointment})

@login_required
def availability(request):
    """Doctor availability view"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    availability = DoctorAvailability.objects.filter(doctor=profile).order_by('weekday')
    
    return render(request, 'doctors/availability.html', {'availability': availability})

@login_required
def edit_availability(request):
    """Edit doctor availability"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Clear existing availability
        DoctorAvailability.objects.filter(doctor=profile).delete()
        
        # Create new availability records
        for day in range(7):  # 0-6 for Monday-Sunday
            start_time = request.POST.get(f'start_time_{day}')
            end_time = request.POST.get(f'end_time_{day}')
            is_available = f'available_{day}' in request.POST
            
            if is_available and start_time and end_time:
                DoctorAvailability.objects.create(
                    doctor=profile,
                    weekday=day,
                    start_time=start_time,
                    end_time=end_time,
                    is_active=True
                )
        
        messages.success(request, 'Availability updated successfully!')
        return redirect('doctors:availability')
    
    # Get existing availability
    availability = {}
    for avail in DoctorAvailability.objects.filter(doctor=profile):
        availability[avail.weekday] = {
            'start_time': avail.start_time,
            'end_time': avail.end_time,
            'is_active': avail.is_active
        }
    
    weekdays = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
        (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]
    
    context = {
        'availability': availability,
        'weekdays': weekdays,
    }
    return render(request, 'doctors/edit_availability.html', context)

@login_required
def patient_records_api(request, patient_id):
    """API endpoint to fetch patient records data"""
    print(f"DEBUG: Accessing patient_records_api for patient_id: {patient_id}")
    print(f"DEBUG: User: {request.user.username}")
    print(f"DEBUG: User groups: {[g.name for g in request.user.groups.all()]}")
    
    if not request.user.groups.filter(name='Doctors').exists():
        print("DEBUG: Access denied - user not in Doctors group")
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    doctor_profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    print(f"DEBUG: Doctor profile: {doctor_profile}, created: {created}")
    
    try:
        patient = get_object_or_404(PatientProfile, id=patient_id)
        print(f"DEBUG: Patient found: {patient.user.username}")
    except Exception as e:
        print(f"DEBUG: Error finding patient: {e}")
        return JsonResponse({'error': f'Patient not found: {e}'}, status=404)
    
    # Check if this doctor has treated this patient
    patient_appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        patient=patient
    )
    print(f"DEBUG: Found {patient_appointments.count()} appointments between doctor and patient")
    
    # For now, allow access if doctor exists - can be made more restrictive later
    # if not patient_appointments.exists():
    #     return JsonResponse({'error': 'You do not have access to this patient\'s records'}, status=403)
    
    # Get patient's medical records
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-date_created')
    print(f"DEBUG: Found {medical_records.count()} medical records for patient")
    
    # Get appointment history with this doctor
    appointment_history = Appointment.objects.filter(
        doctor=doctor_profile,
        patient=patient
    ).order_by('-appointment_date')
    print(f"DEBUG: Found {appointment_history.count()} appointments in history")
    
    # Prepare medical records data
    records_data = []
    for record in medical_records:
        print(f"DEBUG: Processing record: {record.title}")
        records_data.append({
            'id': record.id,
            'title': record.title,
            'record_type': record.record_type,
            'record_type_display': record.get_record_type_display(),
            'description': record.description,
            'date_created': record.date_created.strftime('%b %d, %Y'),
            'file_url': record.file.url if record.file else None,
        })
    
    # Prepare appointments data
    appointments_data = []
    for appointment in appointment_history:
        print(f"DEBUG: Processing appointment: {appointment.appointment_date}")
        appointments_data.append({
            'id': appointment.id,
            'date': appointment.appointment_date.strftime('%b %d, %Y'),
            'time': appointment.appointment_time.strftime('%I:%M %p'),
            'status': appointment.status,
            'status_display': appointment.get_status_display(),
            'reason': appointment.reason,
        })
    
    # Calculate statistics
    total_visits = appointment_history.count()
    completed_visits = appointment_history.filter(status='completed').count()
    print(f"DEBUG: Stats - Total visits: {total_visits}, Completed: {completed_visits}")
    
    data = {
        'patient': {
            'id': patient.id,
            'name': patient.full_name if patient.full_name else patient.user.username,
            'username': patient.user.username,
            'age': patient.age if patient.age else 'Not specified',
        },
        'stats': {
            'total_visits': total_visits,
            'completed_visits': completed_visits,
        },
        'medical_records': records_data,
        'appointments': appointments_data,
    }
    
    print(f"DEBUG: Returning data with {len(records_data)} records and {len(appointments_data)} appointments")
    return JsonResponse(data)

@login_required
def doctor_chat(request):
    """Doctor chat interface with patients for accepted appointments"""
    if not request.user.groups.filter(name='Doctors').exists():
        messages.error(request, 'Access denied. You are not a doctor.')
        return redirect('home')
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    # Get all accepted appointments with their patients
    accepted_appointments = Appointment.objects.filter(
        doctor=profile,
        status='accepted'
    ).select_related('patient__user').order_by('-created_at')
    
    # Get unique patients from accepted appointments
    available_patients = []
    seen_patients = set()
    for appointment in accepted_appointments:
        patient_id = appointment.patient.id
        if patient_id not in seen_patients:
            seen_patients.add(patient_id)
            # Get latest message for this doctor-patient pair
            latest_message = Message.objects.filter(
                appointment__doctor=profile,
                appointment__patient=appointment.patient
            ).order_by('-created_at').first()
            
            available_patients.append({
                'patient': appointment.patient,
                'latest_appointment': appointment,
                'latest_message': latest_message,
                'unread_count': Message.objects.filter(
                    appointment__doctor=profile,
                    appointment__patient=appointment.patient,
                    recipient=request.user,
                    is_read=False
                ).count()
            })
    
    context = {
        'available_patients': available_patients,
        'doctor_profile': profile,
    }
    return render(request, 'doctors/chat.html', context)

@login_required
def get_chat_messages(request, patient_id):
    """Get chat messages with a specific patient"""
    if not request.user.groups.filter(name='Doctors').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Get messages for this doctor-patient pair from any accepted appointment
    # Exclude messages deleted for everyone or deleted for this user
    messages = Message.objects.filter(
        appointment__doctor=profile,
        appointment__patient=patient,
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
    """Send a chat message to a patient"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.groups.filter(name='Doctors').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    import json
    data = json.loads(request.body)
    patient_id = data.get('patient_id')
    content = data.get('content', '').strip()
    
    if not patient_id or not content:
        return JsonResponse({'error': 'Missing patient_id or content'}, status=400)
    
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Find the most recent accepted appointment for this doctor-patient pair
    appointment = Appointment.objects.filter(
        doctor=profile,
        patient=patient,
        status='accepted'
    ).order_by('-created_at').first()
    
    if not appointment:
        return JsonResponse({'error': 'No accepted appointment found'}, status=400)
    
    # Create the message
    message = Message.objects.create(
        appointment=appointment,
        sender=request.user,
        recipient=patient.user,
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
    
    if not request.user.groups.filter(name='Doctors').exists():
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
    
    if not request.user.groups.filter(name='Doctors').exists():
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
def clear_chat(request, patient_id):
    """Clear chat history with a specific patient"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.groups.filter(name='Doctors').exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        profile = get_object_or_404(DoctorProfile, user=request.user)
        patient = get_object_or_404(PatientProfile, id=patient_id)
        
        # Mark all messages as deleted for this user
        messages = Message.objects.filter(
            appointment__doctor=profile,
            appointment__patient=patient,
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