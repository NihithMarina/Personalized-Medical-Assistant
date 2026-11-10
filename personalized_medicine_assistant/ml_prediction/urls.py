from django.urls import path
from . import views

app_name = 'ml_prediction'

urlpatterns = [
    path('api/symptoms/', views.get_symptoms_api, name='get_symptoms_api'),
    path('api/predict/', views.predict_disease_api, name='predict_disease_api'),
    path('prediction/<int:prediction_id>/', views.prediction_detail, name='prediction_detail'),
    path('api/delete-prediction/', views.delete_prediction, name='delete_prediction'),
    path('api/delete-all-predictions/', views.delete_all_predictions, name='delete_all_predictions'),
]