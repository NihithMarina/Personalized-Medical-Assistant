# 🏥 Personalized Medical Assistant (PMA)

A comprehensive Django-based web application that provides personalized healthcare management with AI-powered disease prediction, appointment booking, and medical record management.

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2.6-green.svg)
![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

### 👥 User Management
- **Dual User Types**: Separate portals for patients and doctors
- **Secure Authentication**: Django's built-in authentication system
- **Profile Management**: Comprehensive profile creation and editing

### 🩺 For Patients
- **Disease Prediction**: AI-powered symptom analysis using machine learning
- **Medical Records**: Upload and manage medical documents
- **Appointment Booking**: Schedule appointments with available doctors
- **Medicine Reminders**: Set and manage medication schedules
- **Health Metrics**: BMI calculation and health status tracking
- **Personalized Recommendations**: Diet and treatment suggestions

### 👨‍⚕️ For Doctors
- **Professional Profiles**: Specialization, qualifications, and experience
- **Availability Management**: Set consultation hours and availability
- **Appointment Management**: View and manage patient appointments
- **Patient Consultation**: Access patient information during consultations

### 🤖 Machine Learning Engine
- **Multiple Prediction Models**: Decision Tree, Random Forest, and Enhanced engines
- **Flexible Dataset Support**: Custom CSV dataset integration
- **Symptom Analysis**: Intelligent symptom-to-disease mapping
- **Treatment Recommendations**: Automated medicine and diet suggestions

## 🛠️ Technology Stack

- **Backend**: Django 5.2.6 (Python web framework)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Machine Learning**: Scikit-learn, Pandas, NumPy
- **File Handling**: Pillow for image processing
- **Authentication**: Django's built-in authentication system

## 📁 Project Structure

```
PMA - Personalized Medical Assistant/
├── flask_template/
│   └── personalized_medicine_assistant/
│       ├── .venv/                          # Virtual environment
│       ├── manage.py                       # Django management script
│       ├── requirements.txt                # Python dependencies
│       ├── db.sqlite3                      # Database file
│       │
│       ├── personalized_medicine_assistant/  # Main Django app
│       │   ├── settings.py                 # Django settings
│       │   ├── urls.py                     # URL routing
│       │   └── views.py                    # Main views
│       │
│       ├── patients/                       # Patient management app
│       │   ├── models.py                   # Patient data models
│       │   ├── views.py                    # Patient views
│       │   └── urls.py                     # Patient URL patterns
│       │
│       ├── doctors/                        # Doctor management app
│       │   ├── models.py                   # Doctor data models
│       │   ├── views.py                    # Doctor views
│       │   └── urls.py                     # Doctor URL patterns
│       │
│       ├── ml_prediction/                  # ML prediction engine
│       │   ├── prediction_engine.py        # Main prediction logic
│       │   ├── enhanced_prediction_engine.py
│       │   ├── rf_prediction_engine.py     # Random Forest model
│       │   └── data/                       # ML datasets
│       │       └── dataset_with_recommendations.csv
│       │
│       ├── templates/                      # HTML templates
│       │   ├── base.html                   # Base template
│       │   ├── patients/                   # Patient templates
│       │   └── doctors/                    # Doctor templates
│       │
│       ├── static/                         # Static files (CSS, JS, images)
│       └── media/                          # User uploaded files
└── README.md                               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13 or higher
- pip (Python package installer)
- Git (optional, for cloning)

### Installation

1. **Clone the repository** (or download the ZIP file):
   ```bash
   git clone <repository-url>
   cd "PMA - Personalized Medical Assistant"
   ```

2. **Navigate to the Django project directory**:
   ```bash
   cd flask_template/personalized_medicine_assistant
   ```

3. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

8. **Access the application**:
   - Open your browser and go to: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## 📊 Machine Learning Models

The application includes several prediction engines:

### 1. Basic Decision Tree (`prediction_engine.py`)
- Uses sklearn's DecisionTreeClassifier
- Fast training and prediction
- Good for simple symptom-disease relationships

### 2. Random Forest (`rf_prediction_engine.py`)
- Ensemble method for better accuracy
- Handles complex symptom combinations
- More robust against overfitting

### 3. Enhanced Engine (`enhanced_prediction_engine.py`)
- Advanced preprocessing
- Feature engineering
- Confidence scoring

### Dataset Format
The ML engine supports multiple CSV formats:

```csv
Disease,Symptom_1,Symptom_2,Symptom_3,Medicines,Diet
Flu,fever,cough,body_aches,"Antivirals, rest","Fluids, vitamin C"
Diabetes,blurred_vision,excessive_thirst,frequent_urination,Metformin,"Low carb diet"
```

## 🎯 Key Features Explained

### Disease Prediction
1. **Symptom Input**: Patients enter their symptoms through an intuitive interface
2. **ML Processing**: Multiple algorithms analyze symptom patterns
3. **Prediction Results**: Ranked list of possible conditions with confidence scores
4. **Recommendations**: Suggested treatments, medications, and dietary advice

### Appointment System
1. **Doctor Discovery**: Browse doctors by specialization
2. **Availability Check**: Real-time availability checking
3. **Booking**: Seamless appointment scheduling
4. **Management**: View and manage upcoming appointments

### Medical Records
1. **File Upload**: Support for PDF and image files
2. **Secure Storage**: Files stored securely with proper access controls
3. **Organization**: Categorized by date and type
4. **Sharing**: Share records with doctors during consultations

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root for production settings:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### Database Configuration
For production, update `settings.py` to use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📝 API Documentation

### Disease Prediction API
```python
# Example usage in views
from ml_prediction.prediction_engine import DiseasePredictionEngine

engine = DiseasePredictionEngine()
symptoms = ['fever', 'cough', 'body_aches']
predictions = engine.predict_disease(symptoms)
```

### Model Training
```python
# Train custom model with your dataset
engine.load_and_prepare_data()
engine.train_model()
accuracy = engine.evaluate_model()
```

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

For specific app testing:
```bash
python manage.py test patients
python manage.py test doctors
python manage.py test ml_prediction
```

## 🚀 Deployment

### Using Docker (Recommended)
```dockerfile
FROM python:3.13
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Using Heroku
1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: python manage.py runserver 0.0.0.0:$PORT
   ```
3. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku run python manage.py migrate
   ```

## 🔒 Security Considerations

- Change the `SECRET_KEY` in production
- Set `DEBUG = False` in production
- Configure proper `ALLOWED_HOSTS`
- Use HTTPS in production
- Implement proper file upload validation
- Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add some feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page for existing solutions
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

## 🎯 Future Enhancements

- [ ] Real-time chat between patients and doctors
- [ ] Integration with external pharmacy APIs
- [ ] Mobile app development
- [ ] Advanced analytics dashboard
- [ ] Telemedicine video consultations
- [ ] IoT device integration for health monitoring
- [ ] Multi-language support
- [ ] Insurance integration
- [ ] Prescription management system

## 📊 Performance Metrics

- **Response Time**: < 200ms for most operations
- **ML Prediction**: < 1 second for symptom analysis
- **Database Queries**: Optimized with proper indexing
- **File Upload**: Supports files up to 10MB

## 🏥 Medical Disclaimer

**Important**: This application is for educational and informational purposes only. It is not intended to be a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.

---

**Built with ❤️ for better healthcare accessibility**

*Last updated: September 22, 2025*