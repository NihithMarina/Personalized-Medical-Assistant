from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('patients/', views.patients, name='patients'),
    path('patients/<int:patient_id>/records/api/', views.patient_records_api, name='patient_records_api'),
    path('appointments/', views.appointments, name='appointments'),
    path('appointments/accept/<int:appointment_id>/', views.accept_appointment, name='accept_appointment'),
    path('appointments/reject/<int:appointment_id>/', views.reject_appointment, name='reject_appointment'),
    path('appointments/complete/<int:appointment_id>/', views.complete_appointment, name='complete_appointment'),
    path('chat/', views.doctor_chat, name='chat'),
    path('chat/messages/<int:patient_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('chat/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('chat/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('chat/clear/<int:patient_id>/', views.clear_chat, name='clear_chat'),
    path('availability/', views.availability, name='availability'),
    path('availability/edit/', views.edit_availability, name='edit_availability'),
    path('debug-availability/', views.debug_doctor_availability, name='debug_doctor_availability'),
]