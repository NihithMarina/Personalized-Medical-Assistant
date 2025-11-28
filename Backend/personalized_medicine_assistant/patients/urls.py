from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('medicine-reminders/', views.medicine_reminders, name='medicine_reminders'),
    path('medicine-reminders/add/', views.add_medicine_reminder, name='add_medicine_reminder'),
    path('medicine-reminders/edit/<int:reminder_id>/', views.edit_medicine_reminder, name='edit_medicine_reminder'),
    path('medicine-reminders/delete/<int:reminder_id>/', views.delete_medicine_reminder, name='delete_medicine_reminder'),
    path('medical-records/', views.medical_records, name='medical_records'),
    path('medical-records/add/', views.add_medical_record, name='add_medical_record'),
    path('medical-records/delete/<int:record_id>/', views.delete_medical_record, name='delete_medical_record'),
    path('appointments/', views.appointments, name='appointments'),
    path('appointments/<int:appointment_id>/', views.appointment_details, name='appointment_details'),
    path('appointments/book/', views.book_appointment, name='book_appointment'),
    path('appointments/available-doctors/', views.get_available_doctors, name='get_available_doctors'),
    path('disease-prediction/', views.disease_prediction, name='disease_prediction'),
    path('predict-disease/', views.predict_disease_api, name='predict_disease_api'),
    path('predictions/clear-all/', views.clear_all_predictions, name='clear_all_predictions'),
    path('chat/', views.patient_chat, name='chat'),
    path('chat/messages/<int:doctor_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('chat/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('chat/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('chat/clear/<int:doctor_id>/', views.clear_chat, name='clear_chat'),
]