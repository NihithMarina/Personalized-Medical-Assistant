Personalized Medical Assistant

A comprehensive Django-based web application that provides personalized healthcare management with AI-powered disease prediction, appointment booking, and medical record management.

FEATURES

User Management
- Dual User Types: Separate portals for patients and doctors
- Secure Authentication: Django built-in authentication system
- Profile Management: Comprehensive profile creation and editing

For Patients
- Disease Prediction: AI-powered symptom analysis using machine learning
- Medical Records: Upload and manage medical documents
- Appointment Booking: Schedule appointments with available doctors
- Medicine Reminders: Set and manage medication schedules
- Health Metrics: BMI calculation and health status tracking
- Personalized Recommendations: Diet and treatment suggestions
- Messaging System: Communication with doctors

For Doctors
- Professional Profiles: Specialization, qualifications, and experience
- Availability Management: Set consultation hours and availability
- Appointment Management: View and manage patient appointments
- Patient Consultation: Access patient information during consultations

Machine Learning Engine
- Multiple Prediction Models: Decision Tree, Random Forest, and Enhanced engines
- Flexible Dataset Support: Custom CSV dataset integration
- Symptom Analysis: Intelligent symptom-to-disease mapping
- Treatment Recommendations: Automated medicine and diet suggestions

TECHNOLOGY STACK

Backend Framework
- Django 5.2.6 - Python web framework with WSGI application server
- Python 3.13 or higher - Core programming language
- asgiref 3.9.1 - ASGI specification reference implementation

Frontend Technologies
- HTML5 - Markup with Django template engine
- Tailwind CSS 3.x via CDN - Utility-first CSS framework
- Boxicons 2.1.4 via CDN - Icon library
- Custom CSS - Additional styling
- Django Templates - Server-side rendering

Database
- MySQL - Primary production database
  - mysql-connector-python 9.4.0
  - mysqlclient 2.2.7
- SQLite - Development and backup database

Machine Learning and Data Science
- scikit-learn 1.7.2 - Machine learning algorithms including Decision Tree and Random Forest classifiers
- pandas 2.3.2 - Data manipulation and CSV dataset processing
- NumPy 2.3.3 - Numerical computing and array operations
- SciPy 1.16.2 - Scientific computing libraries
- joblib 1.5.2 - Model serialization and persistence
- threadpoolctl 3.6.0 - Thread pool management for numerical libraries

File Processing and Media Handling
- Pillow 11.3.0 - Image processing and manipulation
- openpyxl 3.1.5 - Excel file reading and writing for XLSX files
- et-xmlfile 2.0.0 - XML file handling for Excel processing

Utilities and Supporting Libraries
- python-decouple 3.8 - Environment variable and configuration management
- pytz 2025.2 - Timezone support and datetime handling
- python-dateutil 2.8.2 - Extensions to standard datetime module
- tzdata 2025.2 - Timezone database
- six 1.17.0 - Python 2 and 3 compatibility utilities
- sqlparse 0.5.3 - SQL parsing and formatting

Security and Authentication
- Django Authentication System - Built-in user authentication and authorization
- CSRF Protection - Cross-site request forgery protection
- Password Validators - Secure password validation rules
- Django Middleware - Security, session, and authentication middleware

PROJECT STRUCTURE

PMA - Personalized Medical Assistant/
- flask_template/
  - personalized_medicine_assistant/
    - .venv/ - Virtual environment
    - manage.py - Django management script
    - requirements.txt - Python dependencies
    - db.sqlite3 - SQLite database file
    
    - personalized_medicine_assistant/ - Main Django application
      - settings.py - Django configuration and settings
      - urls.py - URL routing configuration
      - views.py - Main application views
      - wsgi.py - WSGI application entry point
    
    - patients/ - Patient management application
      - models.py - Patient data models including PatientProfile, MedicineReminder, MedicalRecord, Appointment, DiseasePrediction, Message, MessageEditHistory
      - views.py - Patient-related views and logic
      - urls.py - Patient URL patterns
      - apps.py - Patient app configuration
      - migrations/ - Database migrations
    
    - doctors/ - Doctor management application
      - models.py - Doctor data models including DoctorProfile and DoctorAvailability
      - views.py - Doctor-related views and logic
      - urls.py - Doctor URL patterns
      - apps.py - Doctor app configuration
      - migrations/ - Database migrations
    
    - ml_prediction/ - Machine learning prediction engine
      - prediction_engine.py - Main disease prediction logic using Decision Tree
      - enhanced_prediction_engine.py - Enhanced prediction with advanced preprocessing
      - rf_prediction_engine.py - Random Forest prediction model
      - custom_prediction_engine.py - Custom prediction implementation
      - dataset_overlap_engine.py - Dataset overlap analysis
      - analyze_symptoms.py - Symptom analysis utilities
      - analyze_dataset.py - Dataset analysis tools
      - analyze_excel.py - Excel dataset analysis
      - test_engine.py - ML engine testing utilities
      - data/ - Machine learning datasets directory
      - migrations/ - Database migrations
    
    - templates/ - HTML template files
      - base.html - Base template with Tailwind CSS and Boxicons
      - home.html - Homepage template
      - 403.html - Access forbidden page
      - auth/ - Authentication templates
      - patients/ - Patient portal templates
      - doctors/ - Doctor portal templates
      - ml_prediction/ - ML prediction interface templates
    
    - static/ - Static files including CSS and images
    - staticfiles/ - Collected static files for production
    - media/ - User uploaded files and medical records
    - tests/ - Test suite directory
    - htmlcov/ - HTML coverage reports

- README.md - Project documentation

QUICK START GUIDE

Prerequisites

- Python 3.13 or higher
- pip - Python package installer
- MySQL Server - For production database
- Git - Optional, for cloning repository

Installation Steps

1. Clone the repository or download the ZIP file:
   git clone <repository-url>
   cd "PMA - Personalized Medical Assistant"

2. Navigate to the Django project directory:
   cd flask_template/personalized_medicine_assistant

3. Create and activate virtual environment:
   
   On Windows:
   python -m venv .venv
   .venv\Scripts\activate
   
   On macOS or Linux:
   python -m venv .venv
   source .venv/bin/activate

4. Install dependencies:
   pip install -r requirements.txt

5. Configure database settings:
   - Create a .env file or update settings.py with your MySQL credentials
   - Default configuration uses MySQL on localhost port 3300

6. Run database migrations:
   python manage.py migrate

7. Create a superuser for admin access:
   python manage.py createsuperuser

8. Collect static files:
   python manage.py collectstatic

9. Start the development server:
   python manage.py runserver

10. Access the application:
    - Main application: http://127.0.0.1:8000/
    - Admin panel: http://127.0.0.1:8000/admin/

MACHINE LEARNING MODELS

The application includes several prediction engines:

1. Decision Tree Classifier - prediction_engine.py
   - Uses scikit-learn DecisionTreeClassifier
   - Fast training and prediction
   - Suitable for simple symptom-disease relationships
   - Implements data preprocessing and label encoding
   - Supports custom CSV dataset loading

2. Random Forest Classifier - rf_prediction_engine.py
   - Ensemble learning method for improved accuracy
   - Handles complex symptom combinations
   - More robust against overfitting
   - Better generalization on unseen data

3. Enhanced Prediction Engine - enhanced_prediction_engine.py
   - Advanced preprocessing techniques
   - Feature engineering for better predictions
   - Confidence scoring system
   - Improved accuracy metrics

4. Custom Prediction Engine - custom_prediction_engine.py
   - Customizable prediction logic
   - Flexible model parameters

5. Dataset Overlap Engine - dataset_overlap_engine.py
   - Analyzes dataset overlaps
   - Validates data consistency

Dataset Format

The ML engine supports CSV datasets with the following structure:
- Disease column: Name of the disease
- Symptom columns: Multiple columns for symptoms
- Medicines column: Recommended medications
- Diet column: Dietary recommendations

Example format:
Disease,Symptom_1,Symptom_2,Symptom_3,Medicines,Diet
Flu,fever,cough,body_aches,Antivirals and rest,Fluids and vitamin C
Diabetes,blurred_vision,excessive_thirst,frequent_urination,Metformin,Low carb diet

KEY FEATURES IMPLEMENTATION

Disease Prediction System
1. Symptom Input: Patients enter symptoms through web interface
2. ML Processing: Algorithms analyze symptom patterns using trained models
3. Prediction Results: Ranked list of possible conditions with confidence scores
4. Recommendations: Automated medicine and diet suggestions based on predictions

Appointment Management System
1. Doctor Discovery: Browse doctors filtered by specialization
2. Availability Management: Doctors set their consultation hours
3. Booking System: Patients schedule appointments with available doctors
4. Appointment Tracking: Both parties can view and manage appointments

Medical Records Management
1. File Upload: Support for various file formats including PDF and images
2. Secure Storage: Files stored in media directory with access controls
3. Organization: Records categorized by type (lab report, prescription, scan, other)
4. Record Retrieval: Easy access to historical medical documents

Health Metrics Tracking
1. BMI Calculation: Automatic calculation based on height and weight
2. BMI Status: Classification (underweight, normal, overweight, obese)
3. Profile Management: Comprehensive patient information storage

Medicine Reminder System
1. Medication Scheduling: Set frequency (once, twice, thrice, four times, custom)
2. Multiple Time Slots: Support for up to 4 daily reminder times
3. Date Range: Start and end date for medication courses
4. Active Status Tracking: Toggle active/inactive reminders

Messaging System
1. Patient-Doctor Communication: Direct messaging between patients and doctors
2. Message Management: Send, edit, and delete messages
3. Edit History: Track message modifications with timestamps
4. Soft Delete: Messages can be deleted by sender or receiver

CONFIGURATION

Database Configuration

The application uses MySQL as the primary database with the following settings:
- Engine: django.db.backends.mysql
- Default Database Name: personalized_medicine_db
- Default Host: localhost
- Default Port: 3300
- Configuration managed through python-decouple for environment variables

Environment variables can be set for:
- DB_ENGINE
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST
- DB_PORT

SQLite is available as a backup option for development.

Static Files Configuration

- STATIC_URL: /static/
- STATICFILES_DIRS: Project-level and app-level static directories
- STATIC_ROOT: staticfiles directory for collected static files

Media Files Configuration

- MEDIA_URL: /media/
- MEDIA_ROOT: media directory in project base

Security Settings

- SECRET_KEY: Django secret key (should be changed in production)
- DEBUG: Currently set to True for development
- ALLOWED_HOSTS: 127.0.0.1, localhost, 10.58.3.197
- CSRF Protection: Enabled via CsrfViewMiddleware
- Password Validators: UserAttributeSimilarity, MinimumLength, CommonPassword, NumericPassword

Authentication URLs

- LOGIN_URL: /login/
- LOGIN_REDIRECT_URL: /
- LOGOUT_REDIRECT_URL: /login/

INSTALLED APPLICATIONS

Django Core Apps:
- django.contrib.admin - Admin interface
- django.contrib.auth - Authentication system
- django.contrib.contenttypes - Content types framework
- django.contrib.sessions - Session framework
- django.contrib.messages - Messaging framework
- django.contrib.staticfiles - Static files management

Custom Apps:
- patients - Patient management and features
- doctors - Doctor profiles and availability
- ml_prediction - Machine learning prediction engine

MIDDLEWARE STACK

- SecurityMiddleware - Security enhancements
- SessionMiddleware - Session management
- CommonMiddleware - Common utilities
- CsrfViewMiddleware - CSRF protection
- AuthenticationMiddleware - User authentication
- MessageMiddleware - Message framework
- XFrameOptionsMiddleware - Clickjacking protection

TESTING

Run all tests:
python manage.py test

Run specific app tests:
python manage.py test patients
python manage.py test doctors
python manage.py test ml_prediction

The project includes test files:
- patients/tests.py
- doctors/tests.py
- ml_prediction/test_engine.py
- tests/ directory for integration tests

Coverage reports are generated in htmlcov/ directory.

DEPLOYMENT CONSIDERATIONS

Production Checklist:
1. Change SECRET_KEY to a secure random value
2. Set DEBUG to False
3. Configure proper ALLOWED_HOSTS with your domain
4. Use HTTPS for secure communication
5. Configure production database (MySQL recommended)
6. Set up proper file upload size limits
7. Implement regular backups
8. Enable logging for production monitoring
9. Use environment variables for sensitive data
10. Configure static files serving through web server

Database in Production:
- Use MySQL with proper credentials
- Configure connection pooling
- Set up regular automated backups
- Use sql_mode: traditional for strict SQL compliance

Static Files in Production:
- Run python manage.py collectstatic
- Serve static files through web server (nginx/Apache)
- Use CDN for better performance

Media Files in Production:
- Configure proper file storage backend
- Implement file size and type validation
- Set up virus scanning for uploaded files
- Use cloud storage for scalability

TEMPLATE SYSTEM

The application uses Django template engine with:
- Base template (base.html) with Tailwind CSS via CDN
- Boxicons 2.1.4 for icons via unpkg CDN
- Template inheritance for consistent layout
- Context processors for request, auth, messages, and debug
- Custom templates for auth, patients, doctors, and ml_prediction

DATA MODELS

Patient Models:
- PatientProfile: User profile with health information, BMI tracking
- MedicineReminder: Medication scheduling with multiple time slots
- MedicalRecord: Document storage with categorization
- Appointment: Appointment booking with status tracking
- DiseasePrediction: ML prediction results storage
- Message: Patient-doctor messaging
- MessageEditHistory: Message modification tracking

Doctor Models:
- DoctorProfile: Professional profile with specialization and qualifications
- DoctorAvailability: Consultation hours and availability management

Supported Specializations:
- General Medicine
- Cardiology
- Dermatology
- Neurology
- Orthopedics
- Pediatrics
- Psychiatry
- Surgery
- Gynecology
- Oncology

MEDICAL DISCLAIMER

This application is for educational and informational purposes only. It is not intended to be a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay in seeking it because of something you have read or accessed through this application.
